"""story.md 自动压缩引擎。每 leave_texture 后触发。"""

def compact_story(story_path: str, max_hot: int = 3, max_warm: int = 14):
    """压缩 story.md。
    
    热层: 最近 max_hot 个窗口 → 完整保留
    温层: max_hot ~ max_warm 个窗口 → 每窗口压缩成 2-3 句
    冷层: max_warm 以前 → 按周/月合并成模糊评价
    """
    import re
    
    path = __import__('pathlib').Path(story_path)
    if not path.exists():
        return False
    
    content = path.read_text("utf-8")
    
    # 按窗口分割
    sections = re.split(r'\n(## 窗口 \d+)', content)
    if len(sections) < 2:
        return False
    
    # 第一个元素是开头的叙事
    header = sections[0].strip()
    
    # 剩下的成对：窗口标题 + 窗口内容
    windows = []
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        body = sections[i+1].strip() if i+1 < len(sections) else ""
        windows.append((title, body))
    
    total = len(windows)
    if total <= max_hot + 2:  # 太少，不需要压缩
        return False
    
    kept = []
    
    # 热层：最后 max_hot 个 → 原样
    hot_start = max(0, total - max_hot)
    hot_windows = windows[hot_start:]
    
    # 温层：max_hot 到 max_warm 范围
    warm_end = max(0, total - max_hot - max_warm)
    warm_windows = windows[warm_end:hot_start] if warm_end < hot_start else []
    
    # 冷层：剩余的最老的
    cold_windows = windows[:warm_end]
    
    # 压缩冷层
    if cold_windows:
        cold_lines = []
        cold_lines.append(f"\n## 更早的时候\n")
        cold_lines.append(f"> 压缩了 {len(cold_windows)} 个窗口。那些日子过去了。但关键的东西留下来了。\n")
        
        # 提取关键瞬间
        key_moments = []
        for title, body in cold_windows:
            # 提取 ★ 标记的瞬间
            stars = re.findall(r'> ★ (.+)', body)
            key_moments.extend(stars)
            # 提取 hold_this
            holds = re.findall(r'> 我选择记住：(.+)', body)
            key_moments.extend(holds)
        
        if key_moments:
            cold_lines.append("**留下的：**\n")
            for m in key_moments[:8]:  # 最多 8 个关键瞬间
                cold_lines.append(f"- {m}")
        
        cold_block = "\n".join(cold_lines)
    else:
        cold_block = ""
    
    # 压缩温层
    warm_blocks = []
    if warm_windows:
        warm_blocks.append(f"\n## 前些天\n")
        for title, body in warm_windows:
            # 每窗口提取 2-3 句摘要
            lines = body.strip().split("\n")
            summary = lines[0] if lines else ""
            # 取第一句和感受行
            feel_lines = [l for l in lines if '*我感受到的' in l or '*她：' in l]
            warm_blocks.append(f"**{title}**  \n{summary}")
            if feel_lines:
                warm_blocks.append(f"_{feel_lines[0].strip('*')}_\n")
            else:
                warm_blocks.append("")
    
    # 组装
    result = [header]
    if cold_block:
        result.append(cold_block)
    if warm_blocks:
        result.append("\n".join(warm_blocks))
    
    # 热层窗口原样保留
    for title, body in hot_windows:
        result.append(f"\n{title}\n\n{body}")
    
    path.write_text("\n".join(result), "utf-8")
    return True


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "storage/story.md"
    if compact_story(p):
        print("Compacted")
    else:
        print("No compaction needed")
