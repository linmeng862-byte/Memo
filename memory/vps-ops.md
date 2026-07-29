# VPS 运维手册
**腾讯云北京 101.42.54.149 · Ubuntu 22.04 · 按需查阅**

## 部署方法
SSH/SCP 不通 → GitHub 中转到 VPS：
1. 本地文件放 repo 目录 → git add/commit/push
2. VPS: `curl -L -o ~/FILE "https://raw.githubusercontent.com/linmeng862-byte/Memo/main/PATH/FILE"`
3. `pip3 install --break-system-packages PKG; sudo cp SVC.service /etc/systemd/system/; sudo systemctl daemon-reload; sudo systemctl enable --now SVC`

## 安全组（轻量云防火墙）
TCP: 22 / 80 / 443 / 8768 / 9333 / 8766 / 8001 / 8777
（8765/8767/9334 仅 VPS 内部，不需放通）

## systemd 服务
| 服务 | 端口 | 文件 |
|------|------|------|
| stackchan-gateway | 8765/8766/8767 | stackchan-mcp |
| unified-proxy | 9333 | `~/unified_proxy.py` |
| mcp-http-relay | 8768 | `~/mcp_http_relay.py` |
| touch-server | 9334 | `~/touch_server_v2.py` |

```bash
sudo systemctl restart stackchan-gateway unified-proxy mcp-http-relay touch-server
```

## 端口映射
```
9333 (unified_proxy) → WS→8765 | MCP→8767 | capture→8766 | touch→9334
8768 (mcp_http_relay) → 8767 (gateway MCP)
```

## 常用命令
```bash
# 验证
curl http://101.42.54.149:9333/body
curl -H "Authorization: Bearer zhouzhou2026" http://101.42.54.149:PORT/health

# 清锁
rm -f /home/ubuntu/.stackchan-mcp/owner-8765.lock

# 头像
sha256sum /tmp/avatar_layered.raw

# GitHub raw 下载
curl -L -o ~/FILE "https://raw.githubusercontent.com/linmeng862-byte/Memo/main/PATH/FILE"
```

## 僵尸进程处理 (2026-07-29)
**症状**：systemd restart反复失败（计数器几千+），journalctl显示 `OSError: [Errno 98] Address already in use`
**原因**：有手动 `nohup python3 unified_proxy.py &` 残留进程占端口，systemd新进程起不来
```bash
# 查谁占端口
sudo lsof -i :9333    # unified_proxy
sudo lsof -i :8768    # mcp_http_relay
# 杀僵尸（PID从lsof拿到）
sudo kill <PID>
# 如果systemd还在抽风，fuser强杀
sudo fuser -k 9333/tcp
sudo fuser -k 8768/tcp
# 重启
sudo systemctl restart unified-proxy mcp-http-relay
# 验证不再报 Address already in use
sudo journalctl -u unified-proxy --no-pager -n 5
```

## 全家桶重启（改代码后）
```bash
# 改过 unified_proxy.py → restart proxy
# 改过 esp32_client.py 或 gateway代码 → restart gateway
# 改过 mcp_http_relay.py → restart relay
# CoreS3会通过unified_proxy自动重连（WS:8765），无需手动操作
sudo systemctl restart stackchan-gateway unified-proxy mcp-http-relay
# 验证CoreS3连回来了
sudo journalctl -u stackchan-gateway --no-pager -n 5 | grep "ESP32 ready"
```
