"""Patch server_lite.py to add bobo toy tools"""
import re

path = r'c:\Users\123\.claude\projects\C--Users-123\continuity\server_lite.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add BOBO_NGROK constant
content = content.replace(
    'OB_MCP_URL = os.environ.get("OB_MCP_URL", "https://ye-ombre-brain.zeabur.app/mcp")',
    'OB_MCP_URL = os.environ.get("OB_MCP_URL", "https://ye-ombre-brain.zeabur.app/mcp")\n'
    'BOBO_NGROK = os.environ.get("BOBO_NGROK", "https://harvest-mooing-proposal.ngrok-free.dev")'
)

# 2. Add _bobo_call helper before toy_connect_impl
bobo_helper = '''
def _bobo_call(tool_name, args_dict=None):
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
        except: pass
'''

content = content.replace(
    'def toy_connect_impl(token):',
    bobo_helper + '\ndef toy_connect_impl(token):'
)

# 3. Replace toy_vibrate_impl
old_vib = '''def toy_vibrate_impl(intensity, duration=0.0, suck=-1):
    intensity = max(0, min(100, intensity))
    body = {"intensity": str(intensity), "duration": str(duration)}
    if suck >= 0:
        body["suck"] = str(max(0, min(100, suck)))
    r = _ankni_post("/vibrate", body)
    if r.get("sent"):
        return f"✅ 已发送: {r.get('desc','')} | {r.get('duration','')}"
    return f"❌ 发送失败: {r.get('error', r)}"'''

new_vib = '''def toy_vibrate_impl(intensity, duration=0.0, suck=-1):
    """bobo vibrate"""
    intensity = max(0, min(100, intensity))
    r = _bobo_call("vibrate", {"intensity": intensity})
    if r.get("text"):
        return f"bobo: {r['text']}"
    return f"bobo vibrate fail: {r.get('error', r)}"'''

content = content.replace(old_vib, new_vib)

# 4. Replace toy_stop_impl and add toy_suck_impl
old_stop = '''def toy_stop_impl():
    r = _ankni_post("/stop", {})
    if r.get("stopped"):
        return "✅ 已停止"
    return f"❌ 停止失败: {r.get('error', r)}"'''

new_tools = '''def toy_suck_impl(intensity):
    """bobo suck"""
    intensity = max(0, min(100, intensity))
    r = _bobo_call("suck", {"intensity": intensity})
    if r.get("text"):
        return f"bobo: {r['text']}"
    return f"bobo suck fail: {r.get('error', r)}"

def toy_stop_impl():
    """bobo stop"""
    r = _bobo_call("stop", {})
    if r.get("text"):
        return f"bobo: {r['text']}"
    return f"bobo stop fail: {r.get('error', r)}"'''

content = content.replace(old_stop, new_tools)

# 5. Add toy_suck tool definition
old_def = '    T("toy_vibrate", "控制玩具。intensity: 震动强度 0-100。suck: 吸力强度 0-100（仅双马达，省略则统一用 intensity）。duration: 持续秒数后自停，0=保持到下次指令。",\n      {"intensity": I, "duration": {"type": "number"}, "suck": I}),'
new_def = '    T("toy_vibrate", "啵啵贝震动。intensity: 强度 0-100。", {"intensity": I}),\n    T("toy_suck", "啵啵贝吮吸。intensity: 强度 0-100。", {"intensity": I}),'
content = content.replace(old_def, new_def)

# Update descriptions
content = content.replace(
    'T("toy_stop", "立即停止玩具所有马达。")',
    'T("toy_stop", "停止啵啵贝所有功能。")'
)
content = content.replace(
    'T("toy_connect", "连接粥粥的 Ankni 双马达玩具。token 来自分享链接 https://www.monsterparty.cn/remote/<TOKEN>。每个 token 一次性使用。",\n      {"token": S}, ["token"]),',
    'T("toy_connect", "[已废弃-旧Ankni] 使用 toy_vibrate/toy_suck/toy_stop。", {"token": S}),'
)
content = content.replace(
    'T("toy_status", "查看玩具连接状态。"),',
    'T("toy_status", "啵啵贝连接状态 (ngrok)。"),'
)

# 6. Add dispatch for toy_suck
old_dispatch = '    if name == "toy_vibrate":\n        return text(toy_vibrate_impl(args.get("intensity", 50), args.get("duration", 0.0), args.get("suck", -1)))'
new_dispatch = '    if name == "toy_vibrate":\n        return text(toy_vibrate_impl(args.get("intensity", 50), 0.0, -1))\n    if name == "toy_suck":\n        return text(toy_suck_impl(args.get("intensity", 50)))'
content = content.replace(old_dispatch, new_dispatch)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("server_lite.py patched successfully!")
