import urllib.request
import json
req = urllib.request.Request("http://127.0.0.1:8000/find-healthcare", data=b'{"lat": 0, "lng": 0}', headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
print("STATUS:", res.getcode())
print("BODY:", res.read().decode())
