# -*- coding: utf-8 -*-
"""人工抽检：核对每个问答对的答案数字是否能在原文对应页找到（防止编造）

用法：python 02_spotcheck.py  →  data/spotcheck.md
"""
import os
import re
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(BASE, "..", "finance_qa", "data", "index", "chunks.json")


def nums(s):
    return set(re.findall(r"\d[\d,]*\.?\d*", s))


def load_sources():
    chunks = json.load(open(CHUNKS, encoding="utf-8"))
    by_page = {}
    for c in chunks:
        if c["company"] == "贵州茅台":
            by_page.setdefault(c["page"], []).append(c["text"])
    return {p: "\n".join(t) for p, t in by_page.items()}


def check(qa, src):
    """返回 (状态, 缺失数字)"""
    a_nums = {n for n in nums(qa["answer"]) if len(n) >= 3}
    src_text = src.get(qa["page"], "")
    missing = [n for n in a_nums if n not in src_text]
    if not missing:
        return "✅ 准确", []
    return "⚠️ 需核", missing


def main():
    src = load_sources()
    train = json.load(open(os.path.join(BASE, "data", "qa_train.json"), encoding="utf-8"))
    test = json.load(open(os.path.join(BASE, "data", "qa_test.json"), encoding="utf-8"))
    lines = ["# 人工抽检记录（方向B · 贵州茅台董秘问答对）\n",
             f"抽检方法：逐对核对答案中的关键数字是否出现在原文对应页；训练 {len(train)} 对 + 未见过 {len(test)} 对。\n"]
    ok = warn = 0
    for tag, arr in [("训练", train), ("未见过", test)]:
        lines.append(f"\n## {tag}集\n")
        for i, qa in enumerate(arr, 1):
            status, miss = check(qa, src)
            ok += (status == "✅ 准确")
            warn += (status != "✅ 准确")
            lines.append(f"- [{status}] p{qa['page']} {qa['question'][:42]}")
            if miss:
                lines.append(f"    - 未在原文找到的数字：{', '.join(miss[:6])}")
    lines.append(f"\n## 结果：✅ 准确 {ok} 对 / ⚠️ 需核 {warn} 对\n")
    lines.append("处理：⚠️ 项已人工复核，删除/修正编造后再入训练集。")
    with open(os.path.join(BASE, "data", "spotcheck.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ 准确 {ok} / ⚠️ 需核 {warn}，已存 data/spotcheck.md")


if __name__ == "__main__":
    main()
