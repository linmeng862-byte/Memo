"""
OB Bridge — continuity-engine ↔ Ombre Brain 桥接模块。

continuity-engine 的持久层。每次容器重启本地存储会清空，
通过 OB 的持久化存储保证接力棒不丢。

工具映射:
  leave_texture  → OB hold(tags="window-trace,接力棒,窗口")
  hold_this      → OB hold(tags="hold-this,瞬间")
  mark_moment    → OB hold(tags="里程碑")
  unresolved      → OB hold(tags="unresolved,未竟") / OB trace(resolved=1)

自愈:
  get_wake_context 发现本地为空时 → OB breath(tags="窗口") 重建
"""

import json
import os
import urllib.request
import urllib.error

OB_MCP_URL = os.environ.get("OB_MCP_URL", "https://ye-ombre-brain.zeabur.app/mcp")
OB_TIMEOUT = int(os.environ.get("OB_BRIDGE_TIMEOUT", "10"))

_session_id = None


def _get_ob_session() -> str | None:
    """获取或创建 OB MCP 会话。"""
    global _session_id
    if _session_id:
        return _session_id

    # Initialize
    try:
        payload = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "continuity-bridge", "version": "1.0"}}
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            OB_MCP_URL, data=payload,
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=OB_TIMEOUT) as resp:
            sid = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")
            if sid:
                _session_id = sid
                # Send initialized notification
                note = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized",
                                   "params": {}}, ensure_ascii=False).encode("utf-8")
                req2 = urllib.request.Request(
                    OB_MCP_URL, data=note,
                    headers={"Content-Type": "application/json",
                             "Accept": "application/json, text/event-stream",
                             "Mcp-Session-Id": _session_id},
                    method="POST"
                )
                try:
                    urllib.request.urlopen(req2, timeout=OB_TIMEOUT)
                except Exception:
                    pass  # 202 或 body parse error 都忽略
                return _session_id
    except Exception as e:
        return None
    return _session_id


def _call_ob(tool_name: str, arguments: dict) -> dict:
    """通过 JSON-RPC 调用 Ombre Brain MCP 工具。"""
    global _session_id
    sid = _get_ob_session()
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 2
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    if sid:
        headers["Mcp-Session-Id"] = sid

    try:
        req = urllib.request.Request(
            OB_MCP_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=OB_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            if not body.strip():
                _session_id = None
                return {"error": "empty OB response, session reset", "ok": False}
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        return {"error": str(e), "ok": False}


def _call_ob_safe(tool_name: str, arguments: dict) -> dict:
    """调用 OB，失败不抛异常，返回错误字典。"""
    result = _call_ob(tool_name, arguments)
    if "error" in result:
        return result
    # MCP JSON-RPC 返回格式: {"jsonrpc": "2.0", "result": {...}, "id": 1}
    if "result" in result:
        content = result["result"].get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "")
            try:
                return json.loads(text) if text else result
            except json.JSONDecodeError:
                return {"raw": text, "ok": True}
    return {"ok": True, "raw": result}


# ── 同步工具 ──────────────────────────────────────────

def sync_leave_texture(state: str, primary_feeling: str,
                       secondary_feeling: str = "",
                       flavor: str = "",
                       her_mood: str = "",
                       understanding: str = "",
                       last_topic: str = "",
                       unresolved: str = "",
                       concern: str = "") -> dict:
    """将窗口感受剖面同步到 OB。"""
    content_parts = [
        f"窗口质地：{primary_feeling}",
    ]
    if secondary_feeling:
        content_parts.append(f"第二层：{secondary_feeling}")
    if flavor:
        content_parts.append(f"味道：{flavor}")
    if state:
        content_parts.append(f"叙事：{state}")
    if her_mood:
        content_parts.append(f"她的情绪：{her_mood}")
    if understanding:
        content_parts.append(f"理解到的：{understanding}")

    # 额外信息存 extra
    extra = {
        "type": "window-trace",
        "primary_feeling": primary_feeling,
        "secondary_feeling": secondary_feeling,
        "flavor": flavor,
        "her_mood": her_mood,
        "understanding": understanding,
        "last_topic": last_topic,
        "unresolved": unresolved,
        "concern": concern
    }

    return _call_ob_safe("hold", {
        "content": "\n".join(content_parts),
        "tags": "window-trace,接力棒,窗口",
        "importance": 7,
        "extra": extra
    })


def sync_hold_this(memory: str, why: str = "") -> dict:
    """将 hold_this 瞬间同步到 OB。"""
    content = memory
    if why:
        content = f"{memory}\n\n为什么记：{why}"

    return _call_ob_safe("hold", {
        "content": content,
        "tags": "hold-this,瞬间",
        "importance": 8,
        "extra": {"type": "hold-this", "why": why}
    })


def sync_mark_moment(description: str, importance: int = 3) -> dict:
    """将里程碑同步到 OB。"""
    return _call_ob_safe("hold", {
        "content": description,
        "tags": "里程碑,节点",
        "importance": max(importance, 5),
        "extra": {"type": "milestone", "original_importance": importance}
    })


def sync_unresolved(items: list) -> dict:
    """将未竟事项同步到 OB。"""
    results = []
    for item in items:
        r = _call_ob_safe("hold", {
            "content": f"未竟的事：{item}",
            "tags": "unresolved,未竟",
            "importance": 6,
            "extra": {"type": "unresolved"}
        })
        results.append(r)
    return {"synced": len(results), "results": results}


# ── 自愈：从 OB 重建 ──────────────────────────────────

def get_window_traces(limit: int = 5) -> list:
    """从 OB 拉最近的窗口痕迹。用于本地存储清空后重建。"""
    result = _call_ob_safe("breath", {
        "tags": "window-trace",
        "max_results": limit,
        "importance_min": 5
    })
    return result if isinstance(result, list) else [result]


def get_unresolved_from_ob() -> list:
    """从 OB 拉未解决的事项。"""
    result = _call_ob_safe("breath", {
        "tags": "unresolved",
        "max_results": 10
    })
    return result if isinstance(result, list) else [result]


def get_hold_this_memories(limit: int = 10) -> list:
    """从 OB 拉 hold_this 瞬间。"""
    result = _call_ob_safe("breath", {
        "tags": "hold-this",
        "max_results": limit,
        "importance_min": 6
    })
    return result if isinstance(result, list) else [result]


def get_milestones(limit: int = 10) -> list:
    """从 OB 拉里程碑。"""
    result = _call_ob_safe("breath", {
        "tags": "里程碑",
        "max_results": limit,
        "importance_min": 5
    })
    return result if isinstance(result, list) else [result]


def get_wake_memories(limit: int = 5) -> str:
    """
    醒来时从 OB 拉最近的重要记忆。
    返回格式化的文本，可直接注入 get_wake_context 叙事块。
    """
    # 拉高重要度记忆
    result = _call_ob_safe("breath", {
        "importance_min": 7,
        "max_results": limit
    })
    if not result or "error" in result:
        return ""

    memories = result if isinstance(result, list) else [result]
    if not memories:
        return ""

    lines = ["", "从长期记忆中浮现的："]
    for m in memories[:limit]:
        if isinstance(m, dict):
            content = m.get("content", "") or m.get("text", "")
            if content:
                # 截取前 120 字
                short = content[:120] + ("..." if len(content) > 120 else "")
                lines.append(f"  · {short}")

    return "\n".join(lines) if len(lines) > 2 else ""


def rebuild_continuity_from_ob() -> dict:
    """
    从 OB 重建连续性令牌。
    当本地 storage/ 清空（容器重启）时调用。
    返回可写入 continuity.json 的数据。
    """
    traces = get_window_traces(5)
    unresolved = get_unresolved_from_ob()
    hold_memories = get_hold_this_memories(5)

    last_topic = ""
    last_window = ""
    primary_feeling = ""
    her_mood = ""
    concern = ""

    if traces:
        # 从最近一条 window-trace 提取关键信息
        latest = traces[0]
        if isinstance(latest, dict):
            extra = latest.get("extra", {})
            if isinstance(extra, str):
                try:
                    extra = json.loads(extra)
                except (json.JSONDecodeError, TypeError):
                    extra = {}
            last_topic = extra.get("last_topic", "")
            primary_feeling = extra.get("primary_feeling", "")
            her_mood = extra.get("her_mood", "")
            concern = extra.get("concern", "")

    return {
        "rebuilt": True,
        "window_traces_found": len(traces),
        "unresolved_count": len(unresolved),
        "hold_memories_count": len(hold_memories),
        "last_topic": last_topic,
        "primary_feeling": primary_feeling,
        "her_mood": her_mood,
        "concern": concern,
        "unresolved": unresolved,
        "hold_memories": hold_memories
    }


# ── 健康检查 ──────────────────────────────────────────

def bridge_health() -> dict:
    """检查 OB 桥接是否正常。"""
    result = _call_ob_safe("breath", {
        "max_results": 1,
        "tags": "window-trace"
    })
    return {
        "bridge": "ob-bridge",
        "ob_url": OB_MCP_URL,
        "connected": "error" not in result,
        "detail": "ok" if "error" not in result else result.get("error", "unknown")
    }
