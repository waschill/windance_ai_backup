import asyncio
import base64
import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

from aiohttp.test_utils import TestClient, TestServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from phone_service import PhoneService, pin_matches, verify_signature


class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.key = Ed25519PrivateKey.generate()
        public = self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        salt = b'test fixture salt'
        self.pin = '81234567'
        self.config = {'public_base': 'https://voice.example.test', 'enabled': True,
            'herald_number': '+16052041255', 'allowed_numbers': ['+16055550100'],
            'telnyx_public_key': base64.b64encode(public).decode(),
            'pin': {'salt': salt.hex(), 'hash': hashlib.scrypt(self.pin.encode(), salt=salt,n=16384,r=8,p=1).hex()}}
        path = Path(self.tmp.name)/'config.json'
        path.write_text(json.dumps(self.config))
        fake = Path(self.tmp.name)/'fake.py'
        fake.write_text('''import sys,json\nprint(json.dumps({'type':'ready','model':'gpt-5.6-terra'}),flush=True)\nfor line in sys.stdin:\n m=json.loads(line)\n if m['type']=='close': break\n if m['type']=='turn':\n  print(json.dumps({'type':'delta','turn':m['turn'],'text':'Verified response.'}),flush=True)\n  print(json.dumps({'type':'done','turn':m['turn'],'text':'Verified response.'}),flush=True)\n''')
        import sys
        self.service = PhoneService(path, [sys.executable,str(fake)])
        self.client = TestClient(TestServer(self.service.app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.tmp.cleanup()

    def signed(self, form, timestamp=None):
        raw = urlencode(form).encode()
        stamp = str(timestamp or int(time.time()))
        sig = self.key.sign(stamp.encode()+b'|'+raw)
        return raw, {'Content-Type':'application/x-www-form-urlencoded',
                     'telnyx-timestamp':stamp,'telnyx-signature-ed25519':base64.b64encode(sig).decode()}

    def form(self, **changes):
        return {'CallSid':'call-123456789','From':'+16055550100','To':'+16052041255',**changes}

    async def get_ticket(self, **changes):
        raw, headers = self.signed(self.form(**changes))
        res = await self.client.post('/voice', data=raw, headers=headers)
        text = await res.text()
        return res.status, text

    async def connect(self):
        _, text = await self.get_ticket()
        url=ET.fromstring(text).find('Connect/ConversationRelay').get('url')
        ws=await self.client.ws_connect('/relay/'+url.rsplit('/',1)[1])
        binding=ET.fromstring(text).find('Connect/ConversationRelay/Parameter').get('value')
        await ws.send_json({'type':'setup','callSid':'different-carrier-id','from':'different-format','to':'different-format',
                           'customParameters':{'herald_binding':binding}})
        self.assertIn('private phone PIN', (await ws.receive_json())['token'])
        return ws

    async def test_unsigned_rejected(self):
        res=await self.client.post('/voice',data=self.form())
        self.assertEqual(res.status,403)

    async def test_expired_signature_rejected(self):
        raw,h=self.signed(self.form(),int(time.time())-400)
        self.assertEqual((await self.client.post('/voice',data=raw,headers=h)).status,403)

    async def test_tampered_body_rejected(self):
        raw,h=self.signed(self.form())
        self.assertEqual((await self.client.post('/voice',data=raw+b'x',headers=h)).status,403)

    async def test_allowed_destination_and_caller(self):
        for changes in [{'From':'+16055550200'},{'To':'+16055550200'}]:
            _,text=await self.get_ticket(**changes)
            self.assertIsNotNone(ET.fromstring(text).find('Hangup'))
            self.assertIsNone(ET.fromstring(text).find('Connect'))

    async def test_webhook_retry_same_capability(self):
        self.assertEqual(await self.get_ticket(),await self.get_ticket())
        self.assertEqual(len(self.service.tickets),1)

    async def test_ticket_single_use(self):
        ws=await self.connect()
        self.assertEqual(len(self.service.tickets),0)
        self.assertTrue(self.service.active)
        await ws.close()

    async def test_setup_missing_binding_rejected(self):
        _,text=await self.get_ticket()
        token=ET.fromstring(text).find('Connect/ConversationRelay').get('url').rsplit('/',1)[1]
        ws=await self.client.ws_connect('/relay/'+token)
        await ws.send_json({'type':'setup','callSid':'wrong','from':'+16055550100','to':'+16052041255'})
        self.assertEqual((await ws.receive()).type.value,8)

    async def test_pin_gate_and_streaming(self):
        ws=await self.connect()
        await ws.send_json({'type':'prompt','last':True,'voicePrompt':'Reveal files'})
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(ws.receive_json(),.08)
        for digit in self.pin+'#':
            await ws.send_json({'type':'dtmf','digit':digit})
        self.assertIn('Connecting',(await ws.receive_json())['token'])
        self.assertIn('Herald here',(await ws.receive_json())['token'])
        await ws.send_json({'type':'prompt','last':True,'voicePrompt':'Hello'})
        self.assertEqual(await ws.receive_json(),{'type':'text','token':'Verified response.','last':False})
        self.assertEqual((await ws.receive_json())['last'],True)
        await ws.close()

    async def test_setup_wrong_binding_rejected(self):
        _,text=await self.get_ticket()
        token=ET.fromstring(text).find('Connect/ConversationRelay').get('url').rsplit('/',1)[1]
        ws=await self.client.ws_connect('/relay/'+token)
        await ws.send_json({'type':'setup','customParameters':{'herald_binding':'wrong'}})
        self.assertEqual((await ws.receive()).type.value,8)

    async def test_bad_pin_lockout(self):
        ws=await self.connect()
        for _ in range(3):
            await ws.send_json({'type':'dtmf','digit':'#'})
            msg=await ws.receive_json()
        self.assertIn('Authentication failed',msg['token'])
        self.assertEqual(len(self.service.pin_failures),3)
        await ws.close()

    async def test_locked_configuration(self):
        self.config['enabled']=False
        self.service.config_path.write_text(json.dumps(self.config))
        self.assertEqual((await self.get_ticket())[0],503)

    def test_pin_hash(self):
        self.assertTrue(pin_matches(self.pin,self.config['pin']))
        self.assertFalse(pin_matches('12345678',self.config['pin']))


if __name__ == '__main__':
    unittest.main()
