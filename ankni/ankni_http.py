"""
ankni_http.py — Ankni 玩具 HTTP 接口层
纯 stdlib，跑在 VPS 上，管理 daemon 进程并提供 HTTP API。

用法: python3 ankni_http.py [--port 8777]

环境变量:
  ANKNI_SECRET — 共享密钥，Memo 调用时需带 Authorization: Bearer <secret>

端点:
  POST /connect     body: token=<token>
  POST /vibrate     body: intensity=70&suck=50&duration=3.0
  POST /stop        body: (空)
  GET  /status      → JSON
  POST /disconnect  → 杀掉 daemon
"""

import json, os, signal, subprocess, sys, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from argparse import ArgumentParser

DAEMON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ankni_daemon.py")
CMD_FILE    = "/tmp/ankni_cmd"
STATE_FILE  = "/tmp/ankni_state"
SECRET      = os.environ.get("ANKNI_SECRET", "hzdlZ9pQHSN2qPxY3Xv8mKfR7wJ4bTgC")

daemon_proc = None


def _json_reply(data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode()
    return status, body, "application/json"


def _read_state() -> dict | None:
    if not os.path.exists(STATE_FILE):
        return None
    try:
        return json.loads(open(STATE_FILE).read())
    except:
        return None


def _write_cmd(cmd: str):
    with open(CMD_FILE, "w") as f:
        f.write(cmd)


def _kill_daemon():
    global daemon_proc
    if daemon_proc and daemon_proc.poll() is None:
        try:
            daemon_proc.terminate()
            daemon_proc.wait(timeout=3)
        except:
            try:
                daemon_proc.kill()
            except:
                pass
    daemon_proc = None
    for f in [CMD_FILE, STATE_FILE]:
        try: os.unlink(f)
        except: pass


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _check_auth(self) -> bool:
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {SECRET}"

    def _reply(self, status, body, ctype="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode()
        return dict(urllib.parse.parse_qsl(raw))

    def do_POST(self):
        if not self._check_auth():
            s, b, _ = _json_reply({"error": "unauthorized"}, 401)
            return self._reply(s, b)

        global daemon_proc

        if self.path == "/connect":
            body = self._read_body()
            token = body.get("token", "")
            if not token:
                s, b, _ = _json_reply({"error": "token required"}, 400)
                return self._reply(s, b)

            _kill_daemon()
            daemon_proc = subprocess.Popen(
                ["python3", DAEMON_PATH, token],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

            for _ in range(30):
                time.sleep(0.5)
                st = _read_state()
                if st and st.get("ready"):
                    s, b, _ = _json_reply({
                        "connected": True,
                        "pid": st.get("pid", "unknown"),
                        "is_ds": st.get("is_ds", False),
                        "key_type": st.get("key_type", ""),
                        "fd": st.get("sender_fd"),
                    })
                    return self._reply(s, b)
                if st and st.get("error"):
                    _kill_daemon()
                    s, b, _ = _json_reply({"error": st["error"]}, 500)
                    return self._reply(s, b)

            _kill_daemon()
            s, b, _ = _json_reply({"error": "timeout: device not ready"}, 504)
            return self._reply(s, b)

        elif self.path == "/vibrate":
            if not daemon_proc or daemon_proc.poll() is not None:
                s, b, _ = _json_reply({"error": "not connected"}, 503)
                return self._reply(s, b)

            body = self._read_body()
            intensity = int(body.get("intensity", 50))
            suck      = int(body.get("suck", -1))
            duration  = float(body.get("duration", 0))

            st = _read_state()
            is_ds = st.get("is_ds", False) if st else False

            if suck >= 0 and is_ds:
                cmd = f"vib {suck} {intensity} {duration}" if duration > 0 else f"vib {suck} {intensity}"
                desc = f"suck={suck} vib={intensity}"
            else:
                cmd = f"vib {intensity} {duration}" if duration > 0 else f"vib {intensity}"
                desc = f"intensity={intensity}"

            _write_cmd(cmd)
            dur_str = f"for {duration}s" if duration > 0 else "until next command"
            s, b, _ = _json_reply({"sent": True, "desc": desc, "duration": dur_str})
            return self._reply(s, b)

        elif self.path == "/stop":
            _write_cmd("stop")
            s, b, _ = _json_reply({"stopped": True})
            return self._reply(s, b)

        elif self.path == "/disconnect":
            _write_cmd("quit")
            time.sleep(0.5)
            _kill_daemon()
            s, b, _ = _json_reply({"disconnected": True})
            return self._reply(s, b)

        else:
            s, b, _ = _json_reply({"error": "not found"}, 404)
            return self._reply(s, b)

    def do_GET(self):
        if not self._check_auth():
            s, b, _ = _json_reply({"error": "unauthorized"}, 401)
            return self._reply(s, b)

        if self.path == "/health":
            s, b, _ = _json_reply({"status": "ok"})
            return self._reply(s, b)

        elif self.path == "/status":
            global daemon_proc
            st = _read_state()
            alive = daemon_proc and daemon_proc.poll() is None
            s, b, _ = _json_reply({
                "connected": st.get("ready", False) if st else False,
                "pid": st.get("pid", "") if st else "",
                "is_ds": st.get("is_ds", False) if st else False,
                "key_type": st.get("key_type", "") if st else "",
                "fd": st.get("sender_fd") if st else None,
                "daemon_alive": alive,
            })
            return self._reply(s, b)

        else:
            s, b, _ = _json_reply({"error": "not found"}, 404)
            return self._reply(s, b)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8777)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"ankni-http listening on :{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _kill_daemon()
        server.server_close()
