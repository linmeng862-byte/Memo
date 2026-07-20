import os, sys
os.environ['CONTINUITY_STORAGE_DIR'] = os.environ.get('CONTINUITY_STORAGE_DIR', '/app/storage')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import mcp
import uvicorn
from starlette.middleware.trustedhost import TrustedHostMiddleware

port = int(os.environ.get('PORT', 8001))

# 关键：让 FastMCP 接受所有 Host 头（Zeabur Caddy 代理会改 Host）
mcp.settings.host = "0.0.0.0"
mcp.settings.port = port

app = mcp.streamable_http_app()

# Starlette 层也放行
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

uvicorn.run(app, host='0.0.0.0', port=port, proxy_headers=True, forwarded_allow_ips='*')
