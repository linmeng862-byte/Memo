"""Upload evolution files to Core and re-seed."""
import http.client, json, sys, os

PASSWORD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CORE_PASS", "")
TARBALL = os.path.join(os.path.dirname(__file__), "evo_upload.tar.gz")

c = http.client.HTTPSConnection("core.zeabur.app", timeout=30)
c.request("POST", "/auth/login", body=json.dumps({"password": PASSWORD}), headers={"Content-Type": "application/json"})
r = c.getresponse()
s = r.getheader("Set-Cookie").split("ombre_session=")[1].split(";")[0]
print(f"LOGIN: ok")

with open(TARBALL, "rb") as f:
    data = f.read()
c2 = http.client.HTTPSConnection("core.zeabur.app", timeout=90)
c2.request("POST", "/api/evolution/upload", body=data, headers={"Content-Type": "application/octet-stream", "Cookie": f"ombre_session={s}"})
r2 = c2.getresponse()
print("UPLOAD:", json.dumps(json.loads(r2.read().decode()), indent=2, ensure_ascii=False))

c3 = http.client.HTTPSConnection("core.zeabur.app", timeout=30)
c3.request("POST", "/api/seed", body="{}", headers={"Content-Type": "application/json", "Cookie": f"ombre_session={s}"})
r3 = c3.getresponse()
print("SEED:", json.dumps(json.loads(r3.read().decode()), indent=2, ensure_ascii=False))
