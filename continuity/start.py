import os, sys
os.environ['CONTINUITY_STORAGE_DIR'] = os.environ.get('CONTINUITY_STORAGE_DIR', '/app/storage')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import mcp, STORAGE_DIR, load_continuity
import uvicorn
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.routing import Route
from starlette.responses import JSONResponse, HTMLResponse

# ── 端口 ──────────────────────────────────────────────

_port_raw = os.environ.get('PORT', '8001')
if _port_raw.startswith('$'):
    _port_raw = '8001'
port = int(_port_raw)

mcp.settings.host = "0.0.0.0"
mcp.settings.port = port

app = mcp.streamable_http_app()

# FastMCP 自带 TrustedHostMiddleware，Zaebur Caddy 改 Host 导致 421
# 用 user_middleware 替换掉默认的 host 检查，允许所有 Host
from starlette.middleware import Middleware
app.user_middleware = [Middleware(TrustedHostMiddleware, allowed_hosts=["*"])]
app.middleware_stack = app.build_middleware_stack()

# ── 自定义 HTTP 路由 ──────────────────────────────────

async def root(request):
    cont = load_continuity()
    return JSONResponse({
        "name": "continuity-engine",
        "status": "ok",
        "totalWindows": cont.get("totalWindows", 0),
        "lastClosed": cont.get("lastWindowClosed", ""),
        "endpoints": {"mcp": "/mcp", "dashboard": "/dashboard"}
    })

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

uvicorn.run(app, host='0.0.0.0', port=port, proxy_headers=True, forwarded_allow_ips='*')
