"""Migrate existing hold_this bottles to pinned buckets."""
import http.client, json, sys

PASSWORD = sys.argv[1]

# Login
c = http.client.HTTPSConnection("core.zeabur.app", timeout=30)
c.request("POST", "/auth/login", body=json.dumps({"password": PASSWORD}), headers={"Content-Type": "application/json"})
r = c.getresponse()
s = r.getheader("Set-Cookie").split("ombre_session=")[1].split(";")[0]
print("LOGIN: ok")

# Get bottles
c2 = http.client.HTTPSConnection("core.zeabur.app", timeout=60)
c2.request("GET", "/api/continuity/bottles", headers={"Cookie": f"ombre_session={s}"})
r2 = c2.getresponse()
bottles = json.loads(r2.read().decode()) or []
print(f"Found {len(bottles)} bottles")

# Get existing buckets to avoid duplicates
c3 = http.client.HTTPSConnection("core.zeabur.app", timeout=60)
c3.request("GET", "/api/buckets?limit=500", headers={"Cookie": f"ombre_session={s}"})
r3 = c3.getresponse()
buckets = json.loads(r3.read().decode()) or []
existing_content = set()
for b in buckets:
    ct = (b.get("content_preview") or "")[:100]
    existing_content.add(ct)
print(f"Existing buckets: {len(buckets)}")

# Migrate each bottle
migrated = 0
for b in bottles:
    memory = b.get("memory", "")
    why = b.get("why", "")
    content = f"hold_this: {memory}\n\n为什么记: {why}"
    preview = content[:100]
    if preview in existing_content:
        print(f"  SKIP (exists): {memory[:50]}...")
        continue
    # Create pinned bucket
    c4 = http.client.HTTPSConnection("core.zeabur.app", timeout=30)
    body = json.dumps({"content": content, "tags": "hold-this,瞬间", "importance": 10, "pinned": True, "domain": ["记忆"]})
    c4.request("POST", "/api/bucket/_create", body=body, headers={"Content-Type": "application/json", "Cookie": f"ombre_session={s}"})
    r4 = c4.getresponse()
    d4 = json.loads(r4.read().decode())
    if d4.get("ok") or d4.get("id"):
        migrated += 1
        print(f"  MIGRATED: {memory[:50]}...")
    else:
        print(f"  FAIL: {d4}")

print(f"\nDone: {migrated} migrated, {len(bottles) - migrated} skipped")
