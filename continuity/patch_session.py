"""Fix _bobo_call: add MCP session init for FastMCP streamable-http"""
path = r'c:\Users\123\.claude\projects\C--Users-123\continuity\server_lite.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''def _bobo_call(tool_name, args_dict=None):
    """Call bobo MCP via ngrok tunnel."""
    import http.client
    from urllib.parse import urlparse
    url = urlparse(BOBO_NGROK)
    conn = http.client.HTTPSConnection(url.hostname, url.port or 443, timeout=30)
    try:
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": tool_name, "arguments": args_dict or {}}}
        data = json.dumps(body)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "ngrok-skip-browser-warning": "1"
        }
        conn.request("POST", "/mcp", body=data, headers=headers)
        resp = conn.getresponse()
        result = resp.read().decode()
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}: {result[:200]}"}
        r = json.loads(result)
        if "error" in r:
            return {"error": r["error"].get("message", str(r["error"]))}
        cnt = r.get("result", {}).get("content", [])
        if cnt and len(cnt) > 0:
            return {"text": cnt[0].get("text", str(cnt))}
        return {"text": str(r)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try: conn.close()
        except: pass'''

new = '''def _bobo_call(tool_name, args_dict=None):
    """Call bobo MCP via ngrok tunnel. Init session first."""
    import http.client
    from urllib.parse import urlparse
    url = urlparse(BOBO_NGROK)
    BH = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "ngrok-skip-browser-warning": "1"
    }

    def _post(method, params, sid=None):
        conn = http.client.HTTPSConnection(url.hostname, url.port or 443, timeout=30)
        try:
            data = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params})
            hdrs = dict(BH)
            if sid: hdrs["mcp-session-id"] = sid
            conn.request("POST", "/mcp", body=data, headers=hdrs)
            resp = conn.getresponse()
            raw = resp.read().decode()
            sid2 = resp.getheader("mcp-session-id", "")
            if resp.status != 200:
                return None, None, {"error": f"HTTP {resp.status}: {raw[:200]}"}
            r = json.loads(raw)
            if "error" in r:
                return None, None, {"error": r["error"].get("message", str(r["error"]))}
            return r, sid2, None
        except Exception as e:
            return None, None, {"error": str(e)}
        finally:
            try: conn.close()
            except: pass

    # init
    _, sid, err = _post("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"server-lite","version":"1.0"}})
    if err: return err
    # call
    r, _, err = _post("tools/call", {"name":tool_name,"arguments":args_dict or {}}, sid)
    if err: return err
    cnt = r.get("result",{}).get("content",[])
    if cnt: return {"text": cnt[0].get("text", str(cnt))}
    return {"text": str(r)}'''

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed! Added MCP session init to _bobo_call.")
else:
    print("ERROR: old _bobo_call not found. Already patched?")
    # Find the current version
    import re
    m = re.search(r'def _bobo_call.*?(?=\n(?:def |# ))', content, re.DOTALL)
    if m:
        print("Current _bobo_call:")
        print(m.group()[:300])
