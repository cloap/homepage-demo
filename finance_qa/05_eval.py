# -*- coding: utf-8 -*-
"""10 道题评测：逐题记录 召回块 + 实际回答（跨公司题逐家取证）"""
import os
import sys
import json
from retrieval import Retriever
from answer import generate_answer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# (题目, 类型, 全景取证指标词)  —— 全景/对比题给指标词，单公司题给 None
QUESTIONS = [
    ("贵州茅台2025年营业收入是多少？", "单公司事实", None),
    ("五粮液2025年归属于上市公司股东的净利润是多少？", "单公司事实", None),
    ("泸州老窖2025年营业收入同比增长了多少？", "单公司事实", None),
    ("贵州茅台2025年的毛利率是多少？", "单公司财务", None),
    ("山西汾酒的实际控制人是谁？", "治理结构", None),
    ("洋河股份2025年的利润分配预案是什么？", "分红方案", None),
    ("舍得酒业2025年业绩变动的主要原因是什么？", "管理层讨论", None),
    ("这12家白酒公司中，2025年营业收入规模最大的是哪一家？", "跨公司全景", "营业收入"),
    ("这12家白酒公司中，2025年净利润增速最快的是哪一家？", "跨公司全景", "净利润同比增长"),
    ("贵州茅台和五粮液2025年谁的营业收入更高？高出多少？", "跨公司对比", "营业收入"),
]


def gather_per_company(metric, companies, r, top_k=3):
    """全景题：逐家公司取证（每家单独检索该指标，避免只召回个别公司）"""
    rows = []
    for c in companies:
        chunks = r.hybrid_search(f"{c} 2025年{metric}", top_k=top_k)
        ev = "；".join(f"p{x['page']} {x['text'][:90]}" for x in chunks[:2])
        rows.append({"company": c, "code": chunks[0]["code"] if chunks else "", "evidence": ev})
    return rows


def main():
    r = Retriever()
    companies = sorted({c["company"] for c in r.chunks})

    results = []
    for q, typ, metric in QUESTIONS:
        if metric:  # 全景/对比：逐家取证后整体回答
            rows = gather_per_company(metric, companies, r)
            answer = generate_answer(q, [
                {"company": x["company"], "section": f"全景取证·{metric}", "page": 0,
                 "text": x["evidence"]} for x in rows
            ])
            retrieved = [{"company": x["company"], "text": x["evidence"]} for x in rows]
        else:  # 单公司：混合检索 top-5 后回答
            top = r.hybrid_search(q, top_k=5)
            retrieved = [{"company": x["company"], "section": x["section"], "page": x["page"],
                          "text": x["text"][:200]} for x in top]
            answer = generate_answer(q, top)
        results.append({"question": q, "type": typ, "retrieved": retrieved, "answer": answer})
        print(f"✓ {typ}｜{q[:22]}… 回答 {len(answer)} 字", flush=True)

    with open(os.path.join(DATA_DIR, "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    lines = []
    for x in results:
        lines.append(f"\n{'=' * 70}\n【{x['type']}】{x['question']}")
        lines.append("\n—— 召回块 ——")
        for c in x["retrieved"]:
            lines.append(f"  [{c['company']} | {c.get('section', '全景')} | p{c.get('page', '-')}] {c['text'][:110]}")
        lines.append("\n—— 实际回答 ——\n" + x["answer"])
    with open(os.path.join(DATA_DIR, "eval_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n完成：{len(results)} 题已存 eval_results.json / eval_report.txt")


if __name__ == "__main__":
    main()
