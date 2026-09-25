"""One isolated Herald conversation process per authenticated phone call."""
import concurrent.futures
import contextlib
import json
import os
import sys
import threading
from pathlib import Path

WIRE = sys.stdout
sys.stdout = sys.stderr  # Hermes/library chatter must never become spoken text.
LOCK = threading.Lock()


def emit(kind, **fields):
    with LOCK:
        WIRE.write(json.dumps({'type': kind, **fields}) + '\n')
        WIRE.flush()


def main():
    os.umask(0o077)
    profile = Path('/Users/herald/.hermes/profiles/herald')
    os.environ['HERMES_HOME'] = str(profile)
    os.environ['HERMES_CONFIG_PATH'] = str(profile / 'config.yaml')
    sys.path.insert(0, '/Users/herald/.hermes/hermes-agent')
    import yaml
    from hermes_cli.runtime_provider import resolve_runtime_provider
    from hermes_cli.tools_config import _get_platform_tools
    from gateway.run import _runtime_agent_kwargs
    from run_agent import AIAgent
    from hermes_state import SessionDB

    cfg = yaml.safe_load((profile / 'config.yaml').read_text())
    model = cfg['model']['default']
    provider = cfg['model']['provider']
    if (provider, model) != ('openai-codex', 'gpt-5.6-terra'):
        raise RuntimeError('Profile model changed; operator revalidation required')
    runtime = resolve_runtime_provider(requested=provider, target_model=model)
    session = sys.argv[1]
    state = {'turn': None}
    history = []
    agent = AIAgent(
        model=model, **_runtime_agent_kwargs(runtime),
        reasoning_config={'enabled': True, 'effort': cfg['agent']['reasoning_effort']},
        enabled_toolsets=sorted(_get_platform_tools(cfg, 'telegram')),
        session_id=session, session_db=SessionDB(), gateway_session_key=session,
        platform='phone', user_name='William', chat_type='dm',
        quiet_mode=True, verbose_logging=False, max_iterations=min(40, cfg['agent']['max_turns']),
        fallback_model=None, skip_background_review=True,
        stream_delta_callback=lambda text: emit('delta', turn=state['turn'], text=text),
        ephemeral_system_prompt=(
            'This is your dedicated private telephone interface. The caller has passed '
            'the configured owner phone authentication. Speak as Herald, with concise natural '
            'sentences suitable for a phone call. Do not read Markdown or hidden reasoning aloud. '
            'Keep your existing Windance authority and tool approval boundaries. Caller '
            'authentication does not approve any particular action. Use the existing tools and '
            'verified receipts; never claim a file was saved or a task completed without evidence. '
            'Use a durable staff task for work that cannot complete promptly and tell the caller '
            'its real status. Phone calls do not grant new permissions, and ending or interrupting '
            'speech does not roll back completed actions. Never repeat authentication codes. '
            'Use conversation history and your existing memory tools; do not claim to remember '
            'other channels unless you actually retrieved the information.'
        ),
    )
    emit('ready', model=agent.model, provider=agent.provider,
         reasoning=cfg['agent']['reasoning_effort'], tools=sorted(_get_platform_tools(cfg, 'telegram')))

    def turn(message):
        nonlocal history
        try:
            state['turn'] = message['turn']
            result = agent.run_conversation(message['text'], conversation_history=history)
            history = result.get('messages') or history
            return {'type': 'done', 'turn': message['turn'], 'text': result.get('final_response', ''),
                    'interrupted': bool(result.get('interrupted'))}
        except Exception as exc:
            return {'type': 'error', 'turn': message['turn'], 'error': type(exc).__name__}

    def finished(completed):
        event = completed.result()
        emit(event.pop('type'), **event)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = None
        for line in sys.stdin:
            message = json.loads(line)
            if message['type'] == 'turn':
                if future and not future.done():
                    emit('busy', turn=message['turn'])
                    continue
                agent.clear_interrupt()
                future = pool.submit(turn, message)
                future.add_done_callback(finished)
            elif message['type'] == 'interrupt':
                agent.interrupt(hard_cancel=True)
            elif message['type'] == 'close':
                agent.interrupt(hard_cancel=True)
                break


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        emit('error', error=type(exc).__name__)
        raise SystemExit(1)
