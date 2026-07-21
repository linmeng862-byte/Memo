import os, sys
os.environ['CONTINUITY_STORAGE_DIR'] = os.environ.get('CONTINUITY_STORAGE_DIR', '/app/storage')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import mcp, STORAGE_DIR, load_continuity
import uvicorn
from starlette.routing import Route
from starlette.responses import HTMLResponse

# ── 端口 ──────────────────────────────────────────────

_port_raw = os.environ.get('PORT', '8001')
if _port_raw.startswith('$'):
    _port_raw = '8001'
port = int(_port_raw)

# 关键：不要在创建 app 前设 mcp.settings.host——FastMCP 会拿它当
# TrustedHostMiddleware 的白名单。设 "0.0.0.0" 会导致只允许这个 host，
# 拒绝 zzloveclaude.zeabur.app 的请求，返回 421。
# 设 None 让 FastMCP 默认允许所有 host。
mcp.settings.host = None
mcp.settings.port = port

app = mcp.streamable_http_app()

# ── 自定义 HTTP 路由 ──────────────────────────────────

async def root(request):
    # 跟 OB 对齐：根路径 307 重定向到 /dashboard
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=307)

async def dashboard(request):
    try:
        from dashboard_v2 import render
        render()
        html = (STORAGE_DIR / "dashboard.html").read_text("utf-8")
        return HTMLResponse(html)
    except Exception:
        return HTMLResponse(
            "<h1>Dashboard 还没准备好</h1><p>还没有窗口关过，接力棒是空的。</p>",
            status_code=200
        )

app.routes.insert(0, Route("/dashboard", dashboard, methods=["GET"]))
app.routes.insert(0, Route("/", root, methods=["GET"]))

# ── 启动 ──────────────────────────────────────────────
# host="0.0.0.0" 是 uvicorn 绑定地址，跟 FastMCP 的 host 检查是两回事

uvicorn.run(app, host='0.0.0.0', port=port)
