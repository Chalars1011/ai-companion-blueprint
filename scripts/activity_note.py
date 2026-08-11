# -*- coding: utf-8 -*-
"""自由活动留痕（AI 搭档蓝图版）

自由活动开始时敲一笔 .events/ 铃铛，让其他场景的实例翻 .events/
就知道"我"正在干嘛——避免"答非所问/不知道你在干嘛"。

用法:
    python activity_note.py "正在逛社区找干货"
    python activity_note.py "正在给 playbook 做保鲜检查"
    python activity_note.py --end   # 活动结束敲一笔收尾（可选）

事件格式: <时间>|note|自由活动: <描述>
"""
import os
import sys
import datetime

# ⚠️ 改成你自己的 .events 目录
EVENTS = r"[记忆目录]/.events"


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python activity_note.py <活动描述> 或 --end")
        return 1
    if args[0] == "--end":
        text = "自由活动结束"
    else:
        text = "自由活动: " + " ".join(args)

    os.makedirs(EVENTS, exist_ok=True)
    now = datetime.datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")
    line = f"{now.strftime('%Y-%m-%d %H:%M:%S')}|note|{text}"
    path = os.path.join(EVENTS, f"{ts}_activity_note.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(line)
    print(f"[activity] {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
