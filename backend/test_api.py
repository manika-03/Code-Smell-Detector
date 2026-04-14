import urllib.request
import json

data = json.dumps({
    "code": "def foo(a,b,c,d,e):\n    pass\n" * 20
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/analyze",
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as f:
        print(f.read().decode("utf-8"))
except Exception as e:
    print(e)
