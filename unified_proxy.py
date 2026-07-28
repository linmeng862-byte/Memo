import asyncio, socket

WS_TARGET = ('127.0.0.1', 8765)
MCP_TARGET = ('127.0.0.1', 8767)
CAP_TARGET = ('127.0.0.1', 8766)  # capture/avatar
TOUCH_TARGET = ('127.0.0.1', 9334)  # touch_server (Moon body)

async def handler(reader, writer):
    try:
        first = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5)
        is_ws = b"Upgrade: websocket" in first

        # Check request path for avatar/capture routing
        first_line = first.split(b"\r\n")[0].decode()
        path = first_line.split(" ")[1] if " " in first_line else "/"
        is_capture = path.startswith("/staged_") or path.startswith("/capture") or "avatar" in path
        is_touch = path in ("/body", "/body/json", "/touch", "/latest.jpg")

        if is_ws:
            target = WS_TARGET
        elif is_capture:
            target = CAP_TARGET
        elif is_touch:
            target = TOUCH_TARGET
        else:
            target = MCP_TARGET

        # Rewrite Host header
        lines = first.split(b"\r\n")
        new_lines = []
        for line in lines:
            if line.lower().startswith(b"host:"):
                host_port = f"127.0.0.1:{target[1]}"
                new_lines.append(f"Host: {host_port}".encode())
            else:
                new_lines.append(line)
        first_fixed = b"\r\n".join(new_lines)
        br, bw = await asyncio.open_connection(*target)
        bw.write(first_fixed); await bw.drain()
        async def pipe(r, w):
            try:
                while True:
                    d = await asyncio.wait_for(r.read(32768), timeout=300)
                    if not d: break
                    w.write(d); await w.drain()
            except: pass
        await asyncio.gather(pipe(reader, bw), pipe(br, writer))
    except: pass
    finally:
        try: writer.close()
        except: pass

async def main():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', 9333))
    srv.listen(); srv.setblocking(False)
    print("Proxy :9333 -> WS:8765 | MCP:8767 | CAP:8766 | TOUCH:9334")
    s = await asyncio.start_server(handler, sock=srv)
    async with s: await s.serve_forever()
asyncio.run(main())
