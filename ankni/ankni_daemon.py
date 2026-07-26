"""
ankni_daemon.py — MonsterParty / Ankni WebSocket 客户端
运行在 VPS 上，通过文件 IPC 接收指令。

用法: python3 ankni_daemon.py <token>
  Token 来自分享链接: https://www.monsterparty.cn/remote/<TOKEN>
  每个 token 一次性使用，断开后失效。

文件 IPC:
  读 /tmp/ankni_cmd   — 控制指令
  写 /tmp/ankni_state — 连接状态 JSON

指令格式:
  stop                   — 停止所有马达
  vib N [dur]            — 全部马达强度 N
  vib S V [dur]          — 双马达: 吸力=S, 震动=V
  raw [i,...,i] [dur]    — 原始 10 元素数组
  quit                   — 退出

双马达映射 (AKN_DS_SUCKEGG):
  vib[0]   = 吸力泵
  vib[1-4] = 震动马达
  vib[5-9] = 未使用
"""

import asyncio, json, os, sys, urllib.parse, urllib.request
import websockets

CMD_FILE   = "/tmp/ankni_cmd"
STATE_FILE = "/tmp/ankni_state"


def fetch_session(token: str) -> tuple:
    url = f"https://api.monsterparty.cc/main/v1/remote?s={urllib.parse.quote(token)}"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())["data"]
    return data["socket_url"], data["id"], data["user_id"]


async def run(token: str):
    ws_url, sess_id, uid = fetch_session(token)

    # 写初始状态
    with open(STATE_FILE, "w") as f:
        json.dump({"sender_fd": None, "ready": False, "pid": "", "key_type": "", "is_ds": False}, f)

    # ping_interval=None: 禁用 websockets 库自带 ping，只用 op:8 应用层心跳
    async with websockets.connect(
        ws_url,
        additional_headers={
            "Origin": "https://www.monsterparty.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/537.36 Mobile/15E148",
        },
        ping_interval=None,
        ping_timeout=None,
    ) as ws:
        # ── 握手 ──
        await ws.send(json.dumps({
            "op": 2, "id": 8899001, "gender": "male",
            "remoteID": sess_id, "senderID": uid,
            "avatar": "", "nickname": "remote", "lat": 0, "lng": 0, "area": "",
        }))

        sender_fd = None
        pid = ""
        for _ in range(20):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                op = msg.get("op")
                if op == 6:
                    sender_fd = msg["sender"]["fd"]
                if op == 15 and msg.get("conn"):
                    pid = msg.get("pid", "")
                    break
                if "errNo" in msg:
                    with open(STATE_FILE, "w") as f:
                        json.dump({"sender_fd": None, "ready": False, "pid": "", "error": str(msg)}, f)
                    return
            except asyncio.TimeoutError:
                if sender_fd:
                    break

        if not sender_fd:
            with open(STATE_FILE, "w") as f:
                json.dump({"sender_fd": None, "ready": False, "pid": "", "error": "NO_FD"}, f)
            return

        key_type = "suck" if "SUCK" in pid.upper() else "vib"
        is_ds    = "DS"   in pid.upper()

        with open(STATE_FILE, "w") as f:
            json.dump({
                "sender_fd": sender_fd,
                "ready": True,
                "pid": pid,
                "key_type": key_type,
                "is_ds": is_ds,
            }, f)

        # ── 心跳 ──
        async def heartbeat():
            while True:
                await asyncio.sleep(9)
                try:
                    await ws.send(json.dumps({"op": 8}))
                except:
                    break

        asyncio.create_task(heartbeat())

        # ── 指令循环 ──
        while True:
            await asyncio.sleep(0.3)
            if not os.path.exists(CMD_FILE):
                continue

            line = open(CMD_FILE).read().strip()
            try:
                os.unlink(CMD_FILE)
            except:
                pass
            if not line:
                continue

            parts = line.split()
            cmd = parts[0]
            kt  = key_type
            dur = 0.0

            if cmd == "quit":
                break

            elif cmd == "stop":
                vib_val = [0] * 10

            elif cmd == "raw":
                vib_val = json.loads(parts[1])
                dur = float(parts[2]) if len(parts) > 2 else 0.0

            elif cmd in ("vib_k", "suck_k"):
                kt = "vib" if cmd == "vib_k" else "suck"
                n  = int(parts[1])
                vib_val = [n] * 10 if n > 0 else [0] * 10
                dur = float(parts[2]) if len(parts) > 2 else 0.0

            elif cmd == "vib" and is_ds and len(parts) >= 3:
                s, v = int(parts[1]), int(parts[2])
                vib_val = [s, v, v, v, v, 0, 0, 0, 0, 0]
                dur = float(parts[3]) if len(parts) > 3 else 0.0

            else:
                n = int(parts[1]) if cmd != "stop" else 0
                vib_val = [n] * 10 if n > 0 else [0] * 10
                dur = float(parts[2]) if len(parts) > 2 else 0.0

            try:
                await ws.send(json.dumps({"op": 3, "vib": vib_val, "fd": sender_fd, "keyType": kt}))
            except:
                break

            if dur > 0:
                await asyncio.sleep(dur)
                try:
                    await ws.send(json.dumps({"op": 3, "vib": [0] * 10, "fd": sender_fd, "keyType": kt}))
                except:
                    break

    # 清理
    for f in [CMD_FILE, STATE_FILE]:
        try: os.unlink(f)
        except: pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 ankni_daemon.py <token>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
