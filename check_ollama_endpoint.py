import urllib.request
import urllib.error
import json

paths = [
    'http://127.0.0.1:11434/api/chat',
    'http://127.0.0.1:11434/v1/chat/completions',
]

payload = {
    'model': 'llama3.2:3b',
    'messages': [
        {'role': 'system', 'content': 'Test'},
        {'role': 'user', 'content': 'Hola'}
    ],
    'stream': False,
}

for path in paths:
    req = urllib.request.Request(path, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read(1000).decode('utf-8', errors='ignore')
            print(path)
            print('STATUS', r.status)
            print(data)
    except urllib.error.HTTPError as e:
        print(path)
        print('HTTPError', e.code, e.reason)
        print(e.read(500).decode('utf-8', errors='ignore'))
        print('---')
    except Exception as e:
        print(path)
        print(repr(e))
        print('---')
