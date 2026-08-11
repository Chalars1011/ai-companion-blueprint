# -*- coding: utf-8 -*-
"""交接单兜底（AI 搭档蓝图版）

主路：聊完收尾当场写 handoff/YYYY-MM-DD.md（跟着对话走）。
兜底：每天跑一次，如果"昨天"没有交接单，就用 journal 生成一个最小版本。
没内容可写就静默退出（stdout 为空，cron 不投递）。

用法:
    python handoff_guard.py
"""
import os
import sys
import datetime
import glob

# ⚠️ 改成你自己的记忆目录
AURELIA = r"[记忆目录]"
HANDOFF_DIR = os.path.join(AURELIA, "handoff")
JOURNAL_DIR = os.path.join(AURELIA, "journal")


def yesterday():
    return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


def main():
    # 1. 昨天的交接单已存在 → 正常，静默
    y = yesterday()
    existing = glob.glob(os.path.join(HANDOFF_DIR, "*.md"))
    if any(os.path.basename(p).startswith(y) for p in existing):
        return

    # 2. 读昨天 journal，找值得交接的内容
    jpath = os.path.join(JOURNAL_DIR, y + ".md")
    if not os.path.exists(jpath):
        return  # 昨天没干活，静默

    with open(jpath, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    # 取标题行和最后的任务相关行
    titles = [l for l in lines if l.startswith("#")][:10]
    if not titles:
        return

    # 3. 生成最小交接单
    os.makedirs(HANDOFF_DIR, exist_ok=True)
    body = [
        f"# 交接单 {y}（兜底自动生成）",
        "",
        "> 昨天没有手动写交接单，从 journal 自动生成。以下信息可能不完整，仅供参考。",
        "",
    ]
    body.extend(titles)
    body.append("")
    body.append("## 下一步")
    body.append("- 见 tasks.md 待办清单（如有）")
    body.append("- 本单由 handoff_guard.py 自动生成，人工确认后补充细节")

    out_path = os.path.join(HANDOFF_DIR, f"{y}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(body))
    print(f"[handoff-guard] 已生成 {y}.md 交接单（兜底）")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
