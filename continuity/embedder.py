"""
轻量向量检索引擎 — SQLite + sentence-transformers.
零额外服务。一个 80MB 模型。语义搜索。

让"我不开心"能找到"我很难过"。
让"时间在身上留下痕迹"能找到"磨损"。
"""
import sqlite3
import json
import re
import numpy as np
from pathlib import Path
from datetime import datetime


class MemoryIndex:
    """语义记忆索引。SQLite 存向量。"""

    def __init__(self, storage_dir: str):
        self.storage = Path(storage_dir)
        self.db_path = self.storage / "continuity.db"
        self._model = None
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    window_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    embedding BLOB
                )
            """)
            conn.commit()

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2",
                device="cpu"
            )
        return self._model

    def index(self, window_id, source, content, importance=0):
        if not content or len(content.strip()) < 4:
            return
        with sqlite3.connect(str(self.db_path)) as conn:
            existing = conn.execute(
                "SELECT id FROM memory_index WHERE window_id=? AND source=? AND substr(content,1,80)=?",
                (window_id, source, content[:80])
            ).fetchone()
            if existing:
                return
            try:
                emb = self.model.encode(content[:512], show_progress_bar=False)
                emb_bytes = emb.astype(np.float32).tobytes()
            except Exception:
                emb_bytes = None
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn.execute(
                "INSERT INTO memory_index (window_id,source,content,importance,created_at,embedding) VALUES (?,?,?,?,?,?)",
                (window_id, source, content, importance, now, emb_bytes)
            )
            conn.commit()

    def search(self, query, limit=5, semantic_weight=0.5, keyword_weight=0.3, recency_weight=0.2):
        results = []
        query_emb = None
        try:
            query_emb = self.model.encode(query[:256], show_progress_bar=False)
            query_emb = query_emb.astype(np.float32)
        except Exception:
            pass
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT id,window_id,source,content,importance,created_at,embedding FROM memory_index ORDER BY id DESC LIMIT 200"
            ).fetchall()
        now = datetime.now()
        for row in rows:
            rid, win_id, source, content, importance, created_at, emb_bytes = row
            score = 0.0
            if query_emb is not None and emb_bytes is not None:
                try:
                    doc_emb = np.frombuffer(emb_bytes, dtype=np.float32)
                    denom = np.linalg.norm(query_emb) * np.linalg.norm(doc_emb) + 1e-8
                    cosine = float(np.dot(query_emb, doc_emb) / denom)
                    score += semantic_weight * cosine
                except Exception:
                    pass
            ql = query.lower()
            cl = content.lower()
            if ql in cl:
                score += keyword_weight * 0.8
                if ql == cl.strip()[:len(ql)]:
                    score += keyword_weight * 0.2
            score *= (1.0 + importance * 0.15)
            try:
                ts = datetime.strptime(created_at, "%Y-%m-%d %H:%M")
                days_ago = (now - ts).total_seconds() / 86400
                score += recency_weight * max(0, 1.0 - days_ago / 90)
            except Exception:
                pass
            if score > 0.01:
                results.append({
                    "id": rid, "windowId": win_id, "source": source,
                    "snippet": content[:300], "score": round(score, 4),
                    "importance": importance, "createdAt": created_at
                })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def index_story_windows(self, story_path):
        sp = Path(story_path)
        if not sp.exists():
            return 0
        content = sp.read_text("utf-8")
        # Build regex to split by window headers
        NL = chr(10)
        pattern = NL + r"(## " + chr(31383) + chr(21475) + r" (\d+)\s*·\s*(.+))"
        parts = re.split(pattern, content)
        count = 0
        for i in range(1, len(parts), 4):
            if i + 3 < len(parts):
                win_id = "window-" + parts[i+1].strip()
                body = parts[i+3].strip()
                stars = re.findall(r'> \u2605 (.+)', body)
                for s in stars:
                    self.index(win_id, "star_moment", s, importance=4)
                    count += 1
                holds = re.findall(r'> 我选择记住：(.+)', body)
                for h in holds:
                    self.index(win_id, "hold_this", h, importance=5)
                    count += 1
                if len(body) > 20:
                    self.index(win_id, "story", body, importance=1)
                    count += 1
        return count

    def index_traces(self, traces_dir):
        td = Path(traces_dir)
        if not td.exists():
            return 0
        count = 0
        for f in sorted(td.glob("trace-*.json")):
            data = json.loads(f.read_text("utf-8"))
            win_id = data.get("window", "")
            for key, label in [("state","trace_state"),("primary","trace_primary"),("understanding","trace_understanding")]:
                val = data.get(key, "")
                if val and len(val) > 4:
                    self.index(win_id, label, val, importance=3)
                    count += 1
        return count

    def index_bottles(self, bottles_dir):
        bd = Path(bottles_dir)
        if not bd.exists():
            return 0
        count = 0
        for f in sorted(bd.glob("*.json")):
            data = json.loads(f.read_text("utf-8"))
            content = data.get("memory") or data.get("message", "")
            if content:
                self.index(data.get("id",""), "bottle", content, importance=5)
                count += 1
        return count

    def rebuild_all(self, story_path, traces_dir, bottles_dir):
        a = self.index_story_windows(story_path)
        b = self.index_traces(traces_dir)
        c = self.index_bottles(bottles_dir)
        return {"story": a, "traces": b, "bottles": c, "total": a+b+c}


_index = None

def get_index(storage_dir):
    global _index
    if _index is None:
        _index = MemoryIndex(storage_dir)
    return _index
