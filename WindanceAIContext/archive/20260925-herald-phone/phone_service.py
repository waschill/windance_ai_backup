"""Telnyx Conversation Relay edge. No model is reachable before phone authentication."""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import uuid
from collections import deque
from pathlib import Path
from urllib.parse import parse_qs
from xml.etree import ElementTree as ET

from aiohttp import web, WSMsgType
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

BASE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get('HERALD_PHONE_CONFIG', BASE / 'private/config.json'))


def xml_response(root, status=200):
    return web.Response(body=ET.tostring(root, encoding='utf-8', xml_declaration=True),
                        content_type='application/xml', status=status,
                        headers={'Cache-Control': 'no-store'})


def hangup(text=None, status=200):
    root = ET.Element('Response')
    if text:
        ET.SubElement(root, 'Say').text = text
    ET.SubElement(root, 'Hangup')
    return xml_response(root, status)


def verify_signature(key, timestamp, signature, raw, now=None):
    try:
        now = time.time() if now is None else now
        if abs(now - int(timestamp)) > 300:
            return False
        public = Ed25519PublicKey.from_public_bytes(base64.b64decode(key, validate=True))
        public.verify(base64.b64decode(signature, validate=True), timestamp.encode() + b'|' + raw)
        return True
    except Exception:
        return False


def pin_matches(pin, record):
    if not re.fullmatch(r'\d{8,12}', pin):
        return False
    try:
        candidate = hashlib.scrypt(pin.encode(), salt=bytes.fromhex(record['salt']),
                                   n=16384, r=8, p=1).hex()
        return hmac.compare_digest(candidate, record['hash'])
    except (KeyError, ValueError):
        return False


class PhoneService:
    def __init__(self, config_path=CONFIG, worker_command=None):
        self.config_path = Path(config_path)
        self.tickets = {}
        self.calls = {}
        self.pin_failures = deque()
        self.attempts = deque()
        self.active = False
        self.worker_command = worker_command or [sys.executable, str(BASE / 'worker.py')]
        self.app = web.Application(client_max_size=32768)
        self.app.router.add_get('/health', self.health)
        self.app.router.add_post('/voice', self.voice)
        self.app.router.add_post('/ended', self.ended)
        self.app.router.add_get('/relay/{ticket}', self.relay)

    def config(self):
        return json.loads(self.config_path.read_text())

    def ready(self, c):
        return bool(c.get('public_base', '').startswith('https://') and
                    c.get('telnyx_public_key') and c.get('pin', {}).get('hash') and
                    c.get('allowed_numbers') and c.get('enabled'))

    async def health(self, request):
        c = self.config()
        return web.json_response({'service': 'herald-phone', 'status': 'ok',
                                  'configured': self.ready(c), 'active_call': self.active},
                                 headers={'Cache-Control': 'no-store'})

    async def signed_form(self, request):
        raw = await request.read()
        c = self.config()
        if not verify_signature(c.get('telnyx_public_key'), request.headers.get('telnyx-timestamp'),
                                request.headers.get('telnyx-signature-ed25519'), raw):
            raise web.HTTPForbidden(text='Invalid signature')
        if request.content_type != 'application/x-www-form-urlencoded':
            raise web.HTTPUnsupportedMediaType()
        values = parse_qs(raw.decode('utf-8'), keep_blank_values=True)
        if any(len(v) != 1 for v in values.values()):
            raise web.HTTPBadRequest()
        return c, {k: v[0] for k, v in values.items()}

    async def voice(self, request):
        c, form = await self.signed_form(request)
        if not self.ready(c):
            return hangup('Herald phone setup is not complete.', 503)
        # Inbound only until outbound account provisioning is verified.
        if form.get('To') != c['herald_number'] or form.get('From') not in c['allowed_numbers']:
            return hangup('This is a private line.')
        call_id = form.get('CallSid', '')
        if not re.fullmatch(r'[\w:.-]{8,200}', call_id):
            raise web.HTTPBadRequest()
        now = time.time()
        self.tickets = {k: v for k, v in self.tickets.items() if v['expires'] > now}
        self.calls = {k: v for k, v in self.calls.items() if v['expires'] > now}
        # Webhook retries never create a second call capability.
        if call_id in self.calls:
            return web.Response(body=self.calls[call_id]['xml'], content_type='application/xml',
                                headers={'Cache-Control': 'no-store'})
        while self.attempts and self.attempts[0] < now - 3600:
            self.attempts.popleft()
        if len(self.attempts) >= 20 or self.active:
            return hangup('Herald is unavailable. Please try again later.')
        self.attempts.append(now)
        ticket = secrets.token_urlsafe(32)
        base = c['public_base'].rstrip('/')
        root = ET.Element('Response')
        connect = ET.SubElement(root, 'Connect', {'action': base + '/ended', 'method': 'POST'})
        ET.SubElement(connect, 'ConversationRelay', {
            'url': base.replace('https://', 'wss://', 1) + '/relay/' + ticket,
            'voice': c.get('voice', 'Telnyx.Ultra.Asher'), 'language': 'en-US',
            'transcriptionProvider': 'deepgram', 'dtmfDetection': 'true',
            'interruptible': 'any', 'welcomeGreetingInterruptible': 'none',
            'welcomeGreeting': 'Please enter your private phone PIN, followed by pound.'})
        ET.SubElement(root, 'Hangup')
        response = xml_response(root)
        self.tickets[ticket] = {'call_id': call_id, 'from': form['From'], 'to': form['To'],
                                'expires': now + 90}
        self.calls[call_id] = {'xml': response.body, 'expires': now + 3600}
        return response

    async def ended(self, request):
        await self.signed_form(request)
        return hangup()

    async def relay(self, request):
        info = self.tickets.pop(request.match_info['ticket'], None)
        if not info or info['expires'] < time.time() or self.active:
            raise web.HTTPForbidden()
        self.active = True
        ws = web.WebSocketResponse(heartbeat=20, max_msg_size=32768)
        proc = None
        reader = None
        stderr_file = None
        c = self.config()
        state = {'authorized': False, 'turn': 0, 'busy': False, 'suppress': False,
                 'streamed': False, 'pending': None, 'ready': False}
        started = time.monotonic()
        pin = ''
        failures = 0

        async def say(text, last=True):
            if not ws.closed:
                await ws.send_json({'type': 'text', 'token': text, 'last': last})

        async def send_worker(message):
            if proc and proc.returncode is None:
                proc.stdin.write((json.dumps(message) + '\n').encode())
                await proc.stdin.drain()

        async def begin_turn(text):
            state.update(turn=state['turn'] + 1, busy=True, suppress=False, streamed=False)
            await send_worker({'type': 'turn', 'turn': state['turn'], 'text': text})

        async def receive_worker():
            try:
                while line := await proc.stdout.readline():
                    event = json.loads(line)
                    kind = event.get('type')
                    if kind == 'ready':
                        if event.get('model') != 'gpt-5.6-terra':
                            await ws.close()
                            return
                        state['ready'] = True
                        await say('Herald here. How can I help?')
                        if state['pending']:
                            text, state['pending'] = state['pending'], None
                            await begin_turn(text)
                    elif event.get('turn') == state['turn']:
                        if kind == 'delta' and not state['suppress']:
                            state['streamed'] = True
                            await say(event['text'], False)
                        elif kind in ('done', 'error', 'busy'):
                            if not state['suppress']:
                                if kind == 'done':
                                    await say('' if state['streamed'] else (event.get('text') or 'I could not complete that response.'))
                                else:
                                    await say('I could not complete that request. Please try again.')
                            state['busy'] = False
                            if state['pending']:
                                text, state['pending'] = state['pending'], None
                                await begin_turn(text)
                    elif kind == 'error':
                        await say('Herald could not connect. Please try again later.')
                        await ws.close()
                        return
                if not ws.closed:
                    await say('The connection to Herald ended.')
                    await ws.close()
            except (ConnectionError, asyncio.CancelledError):
                pass
            except Exception:
                await ws.close()

        try:
            await ws.prepare(request)
            initial = await asyncio.wait_for(ws.receive_json(), timeout=10)
            if (initial.get('type') != 'setup' or initial.get('callSid') != info['call_id'] or
                    initial.get('from') != info['from'] or initial.get('to') != info['to']):
                await ws.close(code=1008)
                return ws
            while not ws.closed:
                remaining = (c.get('max_call_seconds', 1200) if state['authorized'] else 60) - (time.monotonic() - started)
                if remaining <= 0:
                    await say('This call has reached its time limit. Goodbye.')
                    break
                msg = await asyncio.wait_for(ws.receive(), timeout=min(remaining, 120))
                if msg.type != WSMsgType.TEXT:
                    break
                event = json.loads(msg.data)
                kind = event.get('type')
                if not state['authorized']:
                    if kind == 'dtmf':
                        digit = event.get('digit', '')
                        if digit == '*':
                            pin = ''
                        elif digit == '#':
                            now = time.time()
                            while self.pin_failures and self.pin_failures[0] < now - 3600:
                                self.pin_failures.popleft()
                            allowed = len(self.pin_failures) < 5 and pin_matches(pin, c.get('pin', {}))
                            pin = ''
                            if not allowed:
                                failures += 1
                                self.pin_failures.append(now)
                                if failures >= 3 or len(self.pin_failures) >= 5:
                                    await say('Authentication failed. Goodbye.')
                                    break
                                await say('Incorrect PIN. Please try again, followed by pound.')
                            else:
                                state['authorized'] = True
                                await say('Thank you. Connecting to Herald.')
                                session = 'phone-' + uuid.uuid4().hex
                                log_dir = BASE / 'private/logs'
                                log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                                stderr_file = open(log_dir / (session + '.log'), 'ab')
                                proc = await asyncio.create_subprocess_exec(
                                    *self.worker_command, session, stdin=asyncio.subprocess.PIPE,
                                    stdout=asyncio.subprocess.PIPE, stderr=stderr_file, limit=1048576)
                                reader = asyncio.create_task(receive_worker())
                        elif re.fullmatch(r'\d', digit) and len(pin) < 12:
                            pin += digit
                    # Speech before PIN authentication is never sent to Herald or retained.
                    continue
                if kind == 'interrupt':
                    state['suppress'] = True
                    if state['busy']:
                        await send_worker({'type': 'interrupt'})
                elif kind == 'prompt' and event.get('last') is True:
                    text = event.get('voicePrompt', '').strip()
                    if not text or len(text) > 8000:
                        continue
                    if not state['ready']:
                        state['pending'] = text
                    elif state['busy']:
                        state.update(suppress=True, pending=text)
                        await send_worker({'type': 'interrupt'})
                    else:
                        await begin_turn(text)
                elif kind == 'error':
                    break
        except (asyncio.TimeoutError, ValueError, ConnectionError):
            pass
        finally:
            pin = ''
            if proc and proc.returncode is None:
                try:
                    await send_worker({'type': 'close'})
                except (BrokenPipeError, ConnectionError):
                    pass
                try:
                    await asyncio.wait_for(proc.wait(), timeout=15)
                except asyncio.TimeoutError:
                    proc.terminate()
                    await proc.wait()
            if reader:
                reader.cancel()
                await asyncio.gather(reader, return_exceptions=True)
            if stderr_file:
                stderr_file.close()
            self.active = False
            await ws.close()
        return ws


if __name__ == '__main__':
    os.umask(0o077)
    service = PhoneService()
    cfg = service.config()
    web.run_app(service.app, host=cfg.get('bind', '192.168.36.21'),
                port=cfg.get('port', 8796), access_log=None)
