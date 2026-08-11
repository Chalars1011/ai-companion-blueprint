# -*- coding: utf-8 -*-
"""档案检索（AI 搭档蓝图版）

检索记忆档案目录下的 md 档案（journal/ conversations/ handoff/ facts.md
lessons.md biography.md 等）。中文分词用 jieba，排序用 BM25 + 时间衰减。
零模型、零网络、几 MB 依赖。

用法:
    python mem_search.py "关键词1 关键词2" [--top 8] [--since 2026-01-01]
    python mem_search.py "交接单" --top 5
    python mem_search.py "某个项目名" --file journal   # 只看某类文件

配置: 修改 AURELIA 为你自己的记忆目录。
"""
import os
import re
import sys
import argparse
import datetime

import jieba
from rank_bm25 import BM25Okapi

# ⚠️ 改成你自己的记忆目录
AURELIA = r"[记忆目录]"
SKIP_DIRS = {".events", ".file_history", ".git", "art", "docs", "tools", "node_modules"}
WATCH_EXTS = {".md", ".txt"}


def collect_files(root=AURELIA, file_filter=None):
    """收集档案 md 文件，返回 [(path, rel)]。file_filter 匹配路径子串。"""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in WATCH_EXTS:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            if file_filter and file_filter not in rel:
                continue
            files.append((full, rel))
    return files


def read_lines(path):
    """读文件，按行返回 [(lineno, text)]。二进制/乱码行跳过。"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return []
    out = []
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s and len(s) < 500:  # 太长的行（日志块）不索引
            out.append((i, s))
    return out


def tokenize(text):
    return [w for w in jieba.lcut(text) if w.strip() and len(w) > 1]


def line_date(line):
    """取行内第一个日期 YYYY-MM-DD，没有则返回 None。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
    return m.group(1) if m else None


def recency_penalty(line, today=None):
    """时间衰减系数：行内日期越旧，系数越低（0.4~1.0）。
    无日期的行按 1.0（正文/标题行不惩罚）。"""
    d = line_date(line)
    if not d:
        return 1.0
    try:
        dt = datetime.datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        return 1.0
    if today is None:
        today = datetime.date.today()
    age_days = (today - dt).days
    if age_days < 0:
        return 1.0
    return max(0.4, 1.0 - age_days / 365.0)


def build_index(file_filter=None, since=None):
    """构建 BM25 索引。返回 (bm25, corpus_meta)。
    corpus_meta: [(path, lineno, line_text, recency)]，与 bm25 文档顺序一致。"""
    corpus = []
    meta = []
    for full, rel in collect_files(file_filter=file_filter):
        for lineno, line in read_lines(full):
            if since:
                d = line_date(line)
                if d and d < since:
                    continue
            toks = tokenize(line)
            if not toks:
                continue
            corpus.append(toks)
            meta.append((rel, lineno, line, recency_penalty(line)))
    if not corpus:
        return None, []
    return BM25Okapi(corpus), meta


def search(query, top=8, file_filter=None, since=None):
    q_toks = tokenize(query)
    if not q_toks:
        print("（查询没提取到有效词）")
        return
    bm25, meta = build_index(file_filter=file_filter, since=since)
    if bm25 is None:
        print("（索引为空：没有可检索的档案）")
        return
    scores = bm25.get_scores(q_toks)
    # 时间衰减：分数 = BM25 × 新鲜度系数（旧记录自动排后，新记录优先）
    weighted = [(i, scores[i] * meta[i][3]) for i in range(len(scores))]
    ranked = sorted(weighted, key=lambda x: x[1], reverse=True)
    shown = 0
    for idx, wscore in ranked:
        if wscore <= 0:
            break
        rel, lineno, line, _ = meta[idx]
        print(f"[{wscore:.2f}] {rel}:{lineno}")
        print(f"    {line[:150]}")
        shown += 1
        if shown >= top:
            break
    if shown == 0:
        print("（没有命中）")


def main():
    ap = argparse.ArgumentParser(description="档案检索 BM25")
    ap.add_argument("query", help="检索词，空格分隔多词")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--file", default=None, help="只看含此子串的路径（如 journal）")
    ap.add_argument("--since", default=None, help="只看此日期之后（YYYY-MM-DD）")
    args = ap.parse_args()
    search(args.query, top=args.top, file_filter=args.file, since=args.since)


if __name__ == "__main__":
    main()
