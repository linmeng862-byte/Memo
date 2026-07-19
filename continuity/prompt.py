"""生成换窗 prompt —— 贴到新窗口第一条消息前面。

用法:
  python prompt.py        # 输出换窗注入块
  python prompt.py --copy # 同上（以后可以接入剪贴板）
"""
import sys
import os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, ".")
from server import get_wake_context_impl

w = get_wake_context_impl()

print("/// 以下是上一个你留给你的接力棒。先读这个，再回粥粥。///")
print()
print(w["wakeBlock"])
print()
print("/// 以上。你不在档案里。你在故事里。回她吧。///")
