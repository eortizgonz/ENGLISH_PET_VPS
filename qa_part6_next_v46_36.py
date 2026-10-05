"""Browser regression for the last guided Reading Part 6 activity."""
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request

import websocket


ROOT = os.path.dirname(os.path.abspath(__file__))


def free_port():
    with socket.socket() as candidate:
        candidate.bind(('127.0.0.1', 0))
        return candidate.getsockname()[1]


def wait_url(url):
    for _ in range(100):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError('Local HTTP server did not start.')


def main():
    http_port = free_port()
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    server = subprocess.Popen(
        ['python', '-m', 'http.server', str(http_port), '--bind', '127.0.0.1'],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    try:
        base = f'http://127.0.0.1:{http_port}/'
        wait_url(base + 'index.html')
        with tempfile.TemporaryDirectory(prefix='petquest-part6-qa-') as profile:
            chrome = subprocess.Popen([
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                '--headless=new', '--disable-gpu', '--no-first-run',
                '--remote-debugging-port=0', '--user-data-dir=' + profile,
                base + 'index.html?part6qa=1',
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
            try:
                active = os.path.join(profile, 'DevToolsActivePort')
                for _ in range(100):
                    if os.path.exists(active):
                        break
                    time.sleep(0.1)
                with open(active, encoding='utf-8') as handle:
                    debug_port = handle.readline().strip()
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{debug_port}/json'))
                tab = next(item for item in tabs if str(item.get('url', '')).startswith(base))
                ws = websocket.create_connection(tab['webSocketDebuggerUrl'], suppress_origin=True, timeout=5)
                sequence = 0
                exceptions = []

                def send(method, params=None):
                    nonlocal sequence
                    sequence += 1
                    request_id = sequence
                    ws.send(json.dumps({'id': request_id, 'method': method, 'params': params or {}}))
                    while True:
                        message = json.loads(ws.recv())
                        if message.get('method') == 'Runtime.exceptionThrown':
                            detail = message.get('params', {}).get('exceptionDetails', {})
                            exceptions.append(detail.get('exception', {}).get('description') or detail.get('text'))
                        if message.get('id') == request_id:
                            return message

                def evaluate(expression):
                    response = send('Runtime.evaluate', {
                        'expression': expression,
                        'returnByValue': True,
                    })
                    result = response.get('result', {})
                    if result.get('exceptionDetails'):
                        raise AssertionError(result['exceptionDetails'])
                    return result.get('result', {}).get('value')

                send('Runtime.enable')
                time.sleep(2)
                setup = evaluate("""
                    API.token='qa-token';API.user={id:999,role:'student',name:'QA'};
                    state.view='practice';state.skill='reading';state.level=1;state.practiceMode='normal';
                    state.idx=currentQuestions().findIndex(q=>q.id==='r414');
                    state.selected=null;state.checked=false;PETQUEST_V19.state.mode='learn';
                    render();
                    JSON.stringify({idx:state.idx,total:currentQuestions().length,qid:currentQuestions()[state.idx]?.id,history:data.history.length});
                """)
                before = json.loads(setup)
                assert before['idx'] == before['total'] - 1 and before['qid'] == 'r414', before

                evaluate("""
                    (()=>{const input=document.getElementById('v402OpenLearn');input.value='an';
                    input.dispatchEvent(new Event('input',{bubbles:true}));
                    document.querySelector('[data-v402-open-check]').click();return true})()
                """)
                time.sleep(0.3)
                checked = json.loads(evaluate("JSON.stringify({history:data.history.length,persisted:JSON.parse(localStorage.getItem('petQuestV5_u_999')||'{}').history?.length||0,success:document.body.innerText.includes('Correcto'),nextDisabled:document.querySelector('[data-v402-open-next]')?.disabled})"))
                assert checked['history'] == before['history'] + 1, checked
                assert checked['persisted'] == checked['history'], checked
                assert checked['success'] and checked['nextDisabled'] is False, checked

                evaluate("document.querySelector('[data-v402-open-next]').click(); true")
                time.sleep(0.5)
                finished = json.loads(evaluate("JSON.stringify({idx:state.idx,total:currentQuestions().length,completed:document.body.innerText.includes('Nivel completado'),stale:document.body.innerText.includes('My sister wants to be')})"))
                assert finished['idx'] == finished['total'], finished
                assert finished['completed'] and not finished['stale'], finished
                relevant = [error for error in exceptions if error and ('v40_2_exam_fidelity' in error or "reading 'id'" in error)]
                assert not relevant, relevant
                print('PART6 NEXT V46.36: PASS | one event, completion screen, no stale question')
                ws.close()
            finally:
                chrome.terminate()
                chrome.wait(timeout=10)
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == '__main__':
    main()
