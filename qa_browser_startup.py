"""Inspect local startup in an isolated headless Chrome profile (no login)."""
import json
import os
import subprocess
import tempfile
import time
import urllib.request
import websocket


def main():
    with tempfile.TemporaryDirectory(prefix='petquest-browser-') as profile:
        proc = subprocess.Popen([
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            '--headless=new', '--disable-gpu', '--no-first-run',
            '--remote-debugging-port=0', '--user-data-dir='+profile, 'about:blank',
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            active = os.path.join(profile, 'DevToolsActivePort')
            for _ in range(100):
                if os.path.exists(active):
                    break
                time.sleep(.1)
            with open(active) as f:
                port = f.readline().strip()
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
            ws = websocket.create_connection(tabs[0]['webSocketDebuggerUrl'], suppress_origin=True, timeout=1)
            for n, method in enumerate(['Runtime.enable', 'Log.enable', 'Page.enable'], 1):
                ws.send(json.dumps({'id': n, 'method': method}))
            ws.send(json.dumps({'id': 4, 'method': 'Page.navigate', 'params': {'url': os.environ.get('PETQUEST_TEST_URL','http://127.0.0.1:8080/')}}))
            deadline = time.time()+12
            while time.time()<deadline:
                try:
                    event = json.loads(ws.recv())
                    if event.get('method') in ['Runtime.exceptionThrown', 'Log.entryAdded']:
                        print(json.dumps(event, ensure_ascii=True))
                except websocket.WebSocketTimeoutException:
                    pass
            ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': 'JSON.stringify({text:document.body.innerText.slice(0,1800),view:typeof state!=="undefined"?state.view:null})', 'returnByValue': True}}))
            while True:
                event = json.loads(ws.recv())
                if event.get('id') == 5:
                    print(json.dumps(event, ensure_ascii=True))
                    break
            ws.close()
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == '__main__':
    main()
