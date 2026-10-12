# -*- coding: utf-8 -*-
"""方向B：从贵州茅台年报生成「投资者问→董秘答」问答对（答案注明页码）

用法：python 01_generate_data.py
输出：data/qa_train.json（训练集）+ data/qa_test.json（未见过题）+ data/four_grid.json（四格题）
"""
import os
import re
import json
import sys
import random
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(BASE, "..", "finance_qa", "data", "index", "chunks.json")
DATA_DIR = os.path.join(BASE, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_env():
    env = {}
    p = os.path.join(BASE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


_ENV = load_env()


def deepseek_chat(messages, max_tokens=600):
    token = _ENV.get("DEEPSEEK_API_KEY", "")
    base = _ENV.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic")
    model = _ENV.get("DEEPSEEK_MODEL", "deepseek-chat")
    url = base.rstrip("/") + "/v1/messages"
    body = json.dumps({"model": model, "max_tokens": max_tokens, "messages": messages}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "x-api-key": token, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    r = urllib.request.urlopen(req, timeout=180)
    data = json.loads(r.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def gen_qa(chunk):
    """从一段原文生成一个问答对，返回 dict 或 None"""
    page = chunk["page"]
    text = chunk["text"].strip()
    if len(text) < 80:
        return None
    user = (
        f"你是上市公司董秘。根据下面这段年报原文，生成一个「投资者会问的问题」和一个「董秘的回答」。\n"
        f"要求：问题具体（涉及数字或事实）；回答严格基于原文、不得编造；用董秘口吻简洁作答。\n"
        f"只输出 JSON：{{\"question\": \"...\", \"answer\": \"...\"}}\n\n"
        f"原文（第{page}页）：\n{text[:900]}"
    )
    out = deepseek_chat([{"role": "user", "content": user}], max_tokens=500).strip()
    m = re.search(r"\{.*\}", out, re.S)
    try:
        d = json.loads(m.group(0))
        q, a = d["question"].strip(), d["answer"].strip()
        if not q or not a:
            return None
        return {"question": q, "answer": a, "page": page, "section": chunk["section"]}
    except Exception:
        return None


def rephrase(q):
    """生成换问法（四格用）"""
    out = deepseek_chat([{"role": "user", "content":
        f"把下面的问题换一种问法（意思完全一样，措辞不同），只输出新问法：\n{q}"}],
        max_tokens=120).strip()
    return out if out else q


def main():
    chunks = json.load(open(CHUNKS, encoding="utf-8"))
    mt = [c for c in chunks if c["company"] == "贵州茅台"]
    # 选文本丰富的块（跳过纯表格和目录），文本 100~1000 字
    cand = [c for c in mt
            if not c["text"].startswith("[表格]")
            and c["section"] not in ("卷首/目录",)
            and 100 <= len(c["text"]) <= 1000]
    # 按章节分层抽样，保证覆盖多个章节
    from collections import defaultdict
    by_sec = defaultdict(list)
    for c in cand:
        by_sec[c["section"]].append(c)
    picked = []
    for sec, arr in by_sec.items():
        arr = sorted(arr, key=lambda x: -len(x["text"]))
        picked.extend(arr[: (50 // len(by_sec)) + 1])
    random.seed(42)
    random.shuffle(picked)
    picked = picked[:50]

    pairs = []
    for i, c in enumerate(picked, 1):
        qa = gen_qa(c)
        if qa:
            pairs.append(qa)
            print(f"[{i}/{len(picked)}] p{c['page']} {c['section'][:8]} → {qa['question'][:30]}", flush=True)

    if len(pairs) < 40:
        print(f"! 只生成 {len(pairs)} 对，不足 40")
    random.shuffle(pairs)
    train = pairs[:40]
    test_unseen = pairs[40:50] if len(pairs) >= 50 else pairs[40:]

    # 四格：训练见过(取10) × 原/换 + 没训练过(test取10) × 原/换
    grid_train = train[:10]
    grid_test = test_unseen[:10]
    four_grid = {"trained_original": [], "trained_rephrased": [],
                 "unseen_original": [], "unseen_rephrased": []}
    for qa in grid_train:
        four_grid["trained_original"].append(qa)
        four_grid["trained_rephrased"].append({**qa, "question": rephrase(qa["question"])})
    for qa in grid_test:
        four_grid["unseen_original"].append(qa)
        four_grid["unseen_rephrased"].append({**qa, "question": rephrase(qa["question"])})

    json.dump(train, open(os.path.join(DATA_DIR, "qa_train.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(test_unseen, open(os.path.join(DATA_DIR, "qa_test.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(four_grid, open(os.path.join(DATA_DIR, "four_grid.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n完成：训练 {len(train)} 对，未见过 {len(test_unseen)} 对，四格 {len(grid_train)}×4")


if __name__ == "__main__":
    main()
