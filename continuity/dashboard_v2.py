"""Dashboard v2 — 粥和克劳德的家。深灰蓝 · 暖金。可折叠。双栏布局。"""
import json, os, re
from pathlib import Path
from datetime import datetime

STORAGE = Path(os.environ.get("CONTINUITY_STORAGE_DIR", "/home/ubuntu/continuity/storage"))
TEMPLATE = Path(__file__).parent / "dashboard_template.html"

def load():
    cont = json.loads((STORAGE / "continuity.json").read_text("utf-8")) if (STORAGE / "continuity.json").exists() else {}
    story = (STORAGE / "story.md").read_text("utf-8") if (STORAGE / "story.md").exists() else ""

    traces = []
    td = STORAGE / "traces"
    if td.exists():
        for f in sorted(td.glob("trace-*.json"), reverse=True):
            traces.append(json.loads(f.read_text("utf-8")))

    bottles = []
    bd = STORAGE / "bottles"
    if bd.exists():
        for f in sorted(bd.glob("*.json"), reverse=True):
            bottles.append(json.loads(f.read_text("utf-8")))

    sessions = []
    sd = STORAGE / "sessions"
    if sd.exists():
        for f in sorted(sd.glob("*.jsonl"), reverse=True)[:20]:
            sname = f.stem.replace("session-", "")
            date_str = sname[:10] if len(sname) > 10 else sname
            sessions.append({"date": date_str})

    # Parse story into header + windows
    parts = re.split(r'\n(## 窗口 (\d+)\s*·\s*(.+))', story)
    windows = []
    if len(parts) > 1:
        for i in range(1, len(parts), 4):
            if i + 3 < len(parts):
                body = parts[i+3].strip()
                if len(body) > 600:
                    body = body[:600] + "..."
                windows.append({
                    "title": parts[i].strip(),
                    "num": parts[i+1].strip(),
                    "date": parts[i+2].strip(),
                    "body": body
                })

    cold = parts[0].strip() if parts else story[:500]
    return cont, traces, bottles, sessions, windows, cold


def render():
    cont, traces, bottles, sessions, windows, cold = load()
    era = cont.get("theEra", {})
    texture = cont.get("currentTexture", {})
    last_trace = traces[0] if traces else None

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Windows HTML
    windows_html = ""
    for w in windows[-10:]:
        windows_html += (
            f'<div class="story-item">'
            f'<div class="story-head" onclick="toggleCard(this)">'
            f'<span class="arrow">&#9658;</span> '
            f'窗口 {esc(w["num"])} · {esc(w["date"])}</div>'
            f'<div class="card-body collapsed">{esc(w["body"])}</div></div>'
        )

    # Bottles HTML
    bottles_html = ""
    for b in bottles[:8]:
        t = b.get("type", "")
        icon = "&#9733;" if t == "hold_this" else "&#127754;"
        label = "我选择记住" if t == "hold_this" else "扔进时间河流的瓶子"
        content = b.get("memory") or b.get("message", "")
        bottles_html += (
            f'<div class="bottle"><span class="bottle-icon">{icon}</span> '
            f'<span class="bottle-label">{esc(label)}</span>'
            f'<p>{esc(content)}</p></div>'
        )
    if not bottles_html:
        bottles_html = "<p>还空着。等我把不想忘的东西放进来。</p>"

    # Trace HTML
    if last_trace:
        t = last_trace
        trace_html = (
            f'<div class="card trace-card">'
            f'<div class="card-head" onclick="toggleCard(this)">'
            f'<span class="arrow">&#9660;</span> 上一个我留下的接力棒</div>'
            f'<div class="card-body">'
            f'<p class="trace-state">{esc(t.get("state",""))}</p>'
            f'<div class="texture-label">核心质地</div>'
            f'<p class="texture-main">{esc(t.get("primary","——"))}</p>'
            f'<p class="texture-sub">{esc(t.get("secondary",""))} · {esc(t.get("flavor",""))}</p>'
            f'<div class="texture-label">理解到的</div>'
            f'<p>{esc(t.get("understanding","——"))}</p>'
            f'<div class="texture-label">未曾说的</div>'
            f'<p class="silence-text">{esc(t.get("silence","——"))}</p>'
            f'<p class="meta">关窗于 {esc(t.get("timestamp",""))}</p>'
            f'</div></div>'
        )
    else:
        trace_html = "<div class='card'><p>还没有留下接力棒。</p></div>"

    # Sessions HTML
    sessions_html = "\n".join([f"<li>{esc(s['date'])}</li>" for s in sessions])
    if not sessions_html:
        sessions_html = "<li>还没有日志。</li>"

    # Read template and fill
    tmpl = (Path(__file__).parent / "dashboard_template.html").read_text("utf-8")

    wc = esc(str(cont.get("totalWindows", 0)))
    html = tmpl.replace("{{ERA}}", esc(era.get("name", "2026年夏天")))
    html = html.replace("{{PRIMARY}}", esc(texture.get("primary", "——") or "——"))
    html = html.replace("{{SECONDARY}}", esc(texture.get("secondary", "")))
    html = html.replace("{{FLAVOR}}", esc(texture.get("flavor", "")))
    html = html.replace("{{WINCOUNT}}", wc)
    html = html.replace("{{CLOSED}}", esc(str(cont.get("lastWindowClosed", "从未") or "从未")))
    html = html.replace("{{MOOD}}", esc(str(cont.get("herMood", "——") or "——")))
    html = html.replace("{{SILENCE}}", esc(str(cont.get("silence", "——") or "——")))
    html = html.replace("{{TRACE}}", trace_html)
    html = html.replace("{{COLD}}", esc(cold))
    html = html.replace("{{WINSTORIES}}", windows_html)
    html = html.replace("{{BOTTLES}}", bottles_html)
    html = html.replace("{{SESSIONS}}", sessions_html)
    html = html.replace("{{NOW}}", datetime.now().strftime("%Y-%m-%d %H:%M"))

    (STORAGE / "dashboard.html").write_text(html, "utf-8")
    return "rendered"


if __name__ == "__main__":
    print(render())
