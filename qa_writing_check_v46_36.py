"""Browser regression for Writing remediation feedback in the V16 builder."""
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


def main():
    http_port = free_port()
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    server = subprocess.Popen(
        ['python', '-m', 'http.server', str(http_port), '--bind', '127.0.0.1'],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    try:
        base = f'http://127.0.0.1:{http_port}/'
        for _ in range(100):
            try:
                if urllib.request.urlopen(base + 'index.html', timeout=1).status == 200:
                    break
            except Exception:
                time.sleep(0.1)
        with tempfile.TemporaryDirectory(prefix='petquest-writing-qa-') as profile:
            chrome = subprocess.Popen([
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                '--headless=new', '--disable-gpu', '--no-first-run',
                '--remote-debugging-port=0', '--user-data-dir=' + profile,
                base + 'index.html?writingqa=1',
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
                    response = send('Runtime.evaluate', {'expression': expression, 'returnByValue': True})
                    result = response.get('result', {})
                    if result.get('exceptionDetails'):
                        raise AssertionError(result['exceptionDetails'])
                    return result.get('result', {}).get('value')

                send('Runtime.enable')
                time.sleep(2)
                text = ('Hi Alex. I joined the science club because I enjoy experiments and building robots. '
                        'We meet every Thursday after school and first we plan our project. Then we work in teams, '
                        'so everyone can share useful ideas. For example, last week we built a small moving car. '
                        'I think you would really enjoy the club because it is friendly and interesting. '
                        'Would you like to come with me next Thursday? We can work together. Best wishes, Sam.')
                evaluate("""
                    API.token='qa-token';API.user={id:999,role:'student',name:'QA'};
                    state.view='writing';state.idx=0;PETQUEST_V16.state.writing.lastStage='final';render();
                """)
                evaluate(f'PETQUEST_V46_13.evaluate({json.dumps(text)}); true')
                time.sleep(0.3)
                count = evaluate("Array.from(document.querySelectorAll('[data-w4613-exercise]')).filter(x=>x.innerText.includes('¿Qué frase añade un detalle útil?')).length")
                assert count == 1, count

                choose = """
                    (index=>{const card=Array.from(document.querySelectorAll('[data-w4613-exercise]')).find(x=>x.innerText.includes('¿Qué frase añade un detalle útil?'));
                    const radio=card.querySelector('input[value="'+index+'"]');radio.checked=true;card.querySelector('[data-w4613-check]').click();return true})
                """
                evaluate(choose + '(0)')
                time.sleep(0.3)
                wrong = json.loads(evaluate("JSON.stringify({host:!!document.getElementById('v16WritingFeedback'),shown:document.body.innerText.includes('❌ Aún no'),status:data.writing.at(-1).weaknesses.find(x=>x.code==='writing-content-detail').exercise.status})"))
                assert wrong == {'host': True, 'shown': True, 'status': 'incorrect'}, wrong

                evaluate(choose + '(1)')
                time.sleep(0.3)
                correct = json.loads(evaluate("JSON.stringify({shown:document.body.innerText.includes('✅ Correcto'),status:data.writing.at(-1).weaknesses.find(x=>x.code==='writing-content-detail').exercise.status})"))
                assert correct == {'shown': True, 'status': 'correct'}, correct
                relevant = [error for error in exceptions if error and 'v46_13_writing_mastery' in error]
                assert not relevant, relevant
                print('WRITING CHECK V46.36: PASS | incorrect and correct feedback rendered')
                ws.close()
            finally:
                chrome.terminate()
                chrome.wait(timeout=10)
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == '__main__':
    main()
