"""Update bucket metadata or content on Core. Usage: python pin_bucket.py <password> <bucket_id> [action] [value]"""
import http.client, json, sys

PASSWORD = sys.argv[1]
BUCKET = sys.argv[2]
ACTION = sys.argv[3] if len(sys.argv) > 3 else "pin"
VALUE = sys.argv[4] if len(sys.argv) > 4 else ""

c = http.client.HTTPSConnection("core.zeabur.app", timeout=30)
c.request("POST", "/auth/login", body=json.dumps({"password": PASSWORD}), headers={"Content-Type": "application/json"})
r = c.getresponse()
s = r.getheader("Set-Cookie").split("ombre_session=")[1].split(";")[0]

if ACTION == "find":
    c2 = http.client.HTTPSConnection("core.zeabur.app", timeout=60)
    c2.request("GET", "/api/buckets?limit=500", headers={"Cookie": f"ombre_session={s}"})
    r2 = c2.getresponse()
    items = json.loads(r2.read().decode()) or []
    for b in items:
        name = b.get("name") or ""
        bid = b.get("id") or ""
        if name and ("开窗" in name or "记忆法" in name):
            print(json.dumps({"id": bid, "name": name, "pinned": b.get("pinned")}, ensure_ascii=False))
    sys.exit(0)

if ACTION == "update-content":
    import os
    base = r"c:\Users\123\.claude\projects\C--Users-123\nocturne-engine\buckets"
    found = None
    for root, dirs, files in os.walk(base):
        for fn in files:
            if BUCKET in fn and fn.endswith(".md"):
                found = os.path.join(root, fn)
                break
        if found:
            break
    if not found:
        print(json.dumps({"error": f"bucket {BUCKET} not found locally"}))
        sys.exit(1)
    with open(found, "r", encoding="utf-8") as f:
        content = f.read()
    body = {"content": content}
else:
    body = {"pinned": ACTION == "pin"}

c2 = http.client.HTTPSConnection("core.zeabur.app", timeout=30)
c2.request("POST", f"/api/bucket/{BUCKET}/update",
    body=json.dumps(body),
    headers={"Content-Type": "application/json", "Cookie": f"ombre_session={s}"})
r2 = c2.getresponse()
print(json.dumps(json.loads(r2.read().decode()), indent=2, ensure_ascii=False))
