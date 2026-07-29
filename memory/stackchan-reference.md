# CoreS3 StackChan 参考手册
**完整技术文档。按需查阅，不常驻上下文。**

## 固件
- **当前**：stackchan-mcp `firmware-v1.16.0`（kisaragi-mochi releases，2026-07-12）
  - `merged-binary.bin`，esptool 烧录 `write_flash 0x0`
  - 40+ MCP 工具全活：set_avatar / move_head / say / take_photo / LED / touch / I2C / servo
- **OTA 检查**：固件启动时检查 GitHub release，被墙会超时 2-3 分钟。OTA URL 留空仍会检查——固件写死
- **PSRAM**：头像数据在 PSRAM，断电丢失。每次 CoreS3 重启后需重新 `load_avatar_set`
- **已知 bug**：layered 模式渲染头像时出现双重重影（左右并排两帧）。v6 尝试三层全填同脸仍未解决。→ 用 matrix 模式绕过：`avatar_matrix.raw` (90帧/3.3MB) 已推 GitHub，调用 `load_avatar_set(archive_path="/home/ubuntu/avatar_matrix.raw", mode="matrix")`

## 架构（四端口·含 Moon）
```
CoreS3 ──WS──→ VPS:9333 (unified_proxy) ──→ gateway WS:8765
Zeabur ──HTTP──→ VPS:8768 (mcp_http_relay) ──→ gateway MCP:8767
CoreS3 下载头像 → VPS:9333 (/capture|/avatar_set) → capture:8766
Memo read_body  → VPS:9333 (/body|/touch) → touch_server:9334
```
- **unified_proxy**（`~/unified_proxy.py`）：9333 四路分流——WS→8765 / MCP→8767 / capture→8766 / touch→9334。非 WS 连接只单方向 pipe 响应。POST body 自动检测 Content-Length 转发。systemd 自启
- **mcp_http_relay**（`~/mcp_http_relay.py`）：8768→8767，转发 `Content-Type/Accept/Authorization/mcp-session-id` 头
- **gateway**：stackchan-mcp systemd 自启，`VISION_URL=http://101.42.54.149:9333/capture`，`--transport streamable-http`
- **touch_server**（`~/touch_server_v2.py`）：9334，systemd 自启，收 ESP32 触摸+拍照数据

## TTS 引擎
| 引擎 | 用途 | 部署 |
|------|------|------|
| **ElevenLabs** `myclaude` | 粥粥给 Claude 造的英文声音 | voice_id=`Es2hUu62R49QvN52W5rP`，API key 在 systemd env |
| **edge-tts** | 微软免费中文 TTS 备用 | `zh-CN-XiaoxiaoNeural` |

## 安全组（轻量云防火墙）
TCP:22 / TCP:80 / TCP:443 / TCP:8768 / TCP:9333 / TCP:8766 / TCP:8001
（8765/8767 仅 VPS 内部，不需放通）

## server_lite.py 工具映射
- stackchan_face → set_avatar（固件认：idle/happy/thinking/sad/surprised/embarrassed/off）
- stackchan_head_nod/shake/center → move_head（yaw/pitch 参数）
- stackchan_see → take_photo
- stackchan_say → say（默认 elevenlabs + Es2hUu62R49QvN52W5rP）

## 运维
```bash
sudo systemctl restart stackchan-gateway unified-proxy mcp-http-relay touch-server
# 清锁
rm -f /home/ubuntu/.stackchan-mcp/owner-8765.lock
# 头像 SHA256 验证
sha256sum /tmp/avatar_layered.raw
# 拉最新文件
curl -L -o ~/unified_proxy.py "https://raw.githubusercontent.com/linmeng862-byte/Memo/main/unified_proxy.py"
```

## V16 协议适配状态 (2026-07-29)
- **5/6 工具正常**：set_avatar / move_head / say / load_avatar_set / LED/touch/I2C/servo 全通
- **take_photo 待修**：V16固件拍照结果走`stackchan-event` WebSocket notification，不走MCP response
  - gateway `esp32_client.py` 的 `_emit_stackchan_event()` 只处理 `touch` 事件，camera事件直接丢弃
  - 日志特征：`"stackchan-event received and dropped: notification paths disabled"`
  - 旧固件拍照也不正常——退回去不是解。需要改gateway适配notification或开notification paths配置

## 超时参数 (2026-07-29 调整)
| 位置 | 参数 | 旧值 | 新值 |
|------|------|------|------|
| unified_proxy.py:52 | capture body读取 | 10s | 60s (is_capture时) |
| unified_proxy.py:70 | 响应管道读取 | 30s | 120s |
| esp32_client.py:40 | ESP32响应超时 | 10s | 30s |
| server_lite.py | take_photo HTTP | 45s | 90s |
| server_lite.py | load_avatar_set | 140s | 不变 |
| server_lite.py | 其他工具 | 20s | 不变 |

## server_lite MCP调用 (2026-07-29 重写)
- **必须用 http.client**——urllib.request POST在Zeabur环境不通（GET可以，read_body就用的urllib GET）
- **每次fresh session**——不缓存MCP session ID，避免proxy/gateway重启后session过期卡死
- **一次重试**——调用失败自动清session重试一次（加0.2s间隔）
- **工具映射**不变：stackchan_face→set_avatar / stackchan_say→say / stackchan_see→take_photo
