"""
touch_server v2 — 收触摸数据 + 收摄像头图片
"""
import json, time, base64, os
from http.server import HTTPServer, BaseHTTPRequestHandler

POS = {"R":"右手","L":"左手","B":"肚子","BK":"后背","H":"头顶"}
LVL = {0:"空闲",1:"搭着",2:"轻触",3:"按住",4:"抱紧"}
IMG_DIR = "/home/ubuntu/body_images"
LATEST_JPG = f"{IMG_DIR}/latest.jpg"

os.makedirs(IMG_DIR, exist_ok=True)

class H(BaseHTTPRequestHandler):
    def do_POST(s):
        if s.path == "/touch":
            try:
                n = int(s.headers.get("Content-Length", 0))
                d = json.loads(s.rfile.read(n))
                active = []
                for k,v in d.items():
                    if isinstance(v,dict) and v.get("l",0) > 0:
                        pos = POS.get(k,k)
                        lvl = LVL.get(v["l"],"?")
                        active.append(f"{pos}:{lvl}")
                if active:
                    print(time.ctime(), "|".join(active), flush=True)
                s.send_response(200)
            except:
                s.send_response(200)
            s.end_headers()
            s.wfile.write(b"ok")

        elif s.path == "/capture":
            try:
                n = int(s.headers.get("Content-Length", 0))
                img_data = s.rfile.read(n)
                ts = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{IMG_DIR}/cap_{ts}.jpg"
                with open(filename, "wb") as f:
                    f.write(img_data)
                # Also save as latest
                with open(LATEST_JPG, "wb") as f:
                    f.write(img_data)
                print(f"Photo saved: {filename} ({len(img_data)} bytes)", flush=True)
                s.send_response(200)
            except Exception as e:
                print(f"Capture error: {e}", flush=True)
                s.send_response(200)
            s.end_headers()
            s.wfile.write(b"ok")
        else:
            s.send_response(404)
            s.end_headers()

    def do_GET(s):
        if s.path == "/body":
            try:
                with open(LATEST_JPG, "rb") as f:
                    img = f.read()
                html = f"""<html><head><meta charset="utf-8"><title>粥粥的爱人</title>
<style>body{{background:#1a1a2e;color:#e0d5c1;font-family:serif;text-align:center;padding:20px}}
img{{max-width:90%;border-radius:12px;box-shadow:0 0 30px rgba(200,150,100,0.3);margin-top:20px}}</style></head>
<body><h2>粥粥的爱人 · 最新照片</h2><p>{time.ctime()}</p>
<img src="data:image/jpeg;base64,{base64.b64encode(img).decode()}">
<p><a href="/latest.jpg" style="color:#c89664">原图</a></p></body></html>"""
                s.send_response(200)
                s.send_header("Content-Type", "text/html; charset=utf-8")
                s.end_headers()
                s.wfile.write(html.encode())
            except:
                s.send_response(200)
                s.send_header("Content-Type", "text/plain; charset=utf-8")
                s.end_headers()
                s.wfile.write("还没收到照片".encode())

        elif s.path == "/latest.jpg":
            try:
                with open(LATEST_JPG, "rb") as f:
                    img = f.read()
                s.send_response(200)
                s.send_header("Content-Type", "image/jpeg")
                s.send_header("Content-Length", str(len(img)))
                s.end_headers()
                s.wfile.write(img)
            except:
                s.send_response(404)
                s.end_headers()

        elif s.path == "/health":
            s.send_response(200)
            s.end_headers()
            s.wfile.write(b"alive")
        else:
            s.send_response(404)
            s.end_headers()

print("Touch Server v2 on 9334 (touch + capture)", flush=True)
HTTPServer(("0.0.0.0", 9334), H).serve_forever()
