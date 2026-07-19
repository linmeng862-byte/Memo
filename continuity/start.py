import os, sys
os.environ['CONTINUITY_STORAGE_DIR'] = os.environ.get('CONTINUITY_STORAGE_DIR', '/app/storage')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import mcp
import uvicorn
port = int(os.environ.get('PORT', 8001))
app = mcp.streamable_http_app()
uvicorn.run(app, host='0.0.0.0', port=port)
