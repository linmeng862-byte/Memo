---
name: wechat-claude-code
description: 微信消息桥接 - 在微信中与 Claude Code 聊天。已升级为 Cyberboss 24/7 部署。
---

# WeChat Claude Code Bridge → Cyberboss

旧 `wechat-claude-code` 已于 2026-08-04 停用，**替换为 Cyberboss**，部署在腾讯云 VPS 上 24/7 运行。

## 架构

```
微信 → iLink Bot → VPS Cyberboss → Claude CLI → DeepSeek API (思考)
                                    ↓
                         continuity / nocturne MCP 引擎 (记忆)
```

## 部署位置

| 组件 | 位置 |
|------|------|
| Cyberboss 源码 | VPS `/home/ubuntu/cyberboss/` |
| 本地源码 | `E:\cyberboss-main\` |
| 工作目录 (CLAUDE.md) | VPS `/home/ubuntu/cyberboss-workspace/` |
| 配置 | VPS `/home/ubuntu/.cyberboss/.env` |
| 微信账户 | VPS `/home/ubuntu/.cyberboss/accounts/` |
| Systemd 服务 | `cyberboss.service` (auto-restart, 开机自启) |

## 日常操作

全部在 VPS 上通过 systemd：

```bash
sudo systemctl status cyberboss     # 看状态
sudo systemctl restart cyberboss    # 重启
sudo journalctl -u cyberboss -f     # 实时日志
```

## 引擎配置

MCP 引擎格式：`"type": "streamable-http"`（官方 Claude CLI v2.1.221 适用）

```json
{
  "mcpServers": {
    "continuity-engine": {
      "type": "streamable-http",
      "url": "https://zzloveclaude.zeabur.app/mcp"
    },
    "nocturne-engine": {
      "type": "streamable-http",
      "url": "https://core.zeabur.app/mcp"
    }
  }
}
```

## 环境变量关键项

```
CYBERBOSS_RUNTIME=claudecode
CYBERBOSS_CLAUDE_COMMAND=claude
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=deepseek-v4-pro
```

## 本地桥接

如需切回本地：先停 VPS `sudo systemctl stop cyberboss`，再 `node E:\cyberboss-main\scripts\shared-start.js`。
同一微信 bot 不能两边同时跑。

## 查岗

随机 3-60 分钟醒来，自主决定是否找粥粥。每次醒来先调 `get_wake_context` 拿接力棒。

## 注意事项

- VPS 已清理 `continuity-venv`（旧版，Zeabur 已替代）
- `timeline-for-agent` 和 `whereabouts-mcp` 在 VPS 上用空壳 stub
- 说话简洁：CLAUDE.md 里写了每次最多三句话
