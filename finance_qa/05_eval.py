# -*- coding: utf-8 -*-
"""10 道题评测：逐题记录召回块（公司/章节/页码）"""
import os
import json
from retrieval import Retriever

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# (题目, 类型)
QUESTIONS = [
    ("贵州茅台2025年营业收入是多少？", "单公司事实"),
    ("五粮液2025年归属于上市公司股东的净利润是多少？", "单公司事实"),
    ("泸州老窖2025年营业收入同比增长了多少？", "单公司事实"),
    ("贵州茅台2025年的毛利率是多少？", "单公司财务"),
    ("山西汾酒的实际控制人是谁？", "治理结构"),
    ("洋河股份2025年的利润分配预案是什么？", "分红方案"),
    ("舍得酒业2025年业绩变动的主要原因是什么？", "管理层讨论"),
    ("这12家白酒公司中，2025年营业收入规模最大的是哪一家？", "跨公司全景"),
    ("这12家白酒公司中，2025年净利润增速最快的是哪一家？", "跨公司全景"),
    ("贵州茅台和五粮液2025年谁的营业收入更高？高出多少？", "跨公司对比"),
]


def main():
    r = Retriever()
    results = []
    report_lines = []
    for q, typ in QUESTIONS:
        top = r.hybrid_search(q, top_k=5)
        results.append({
            "question": q,
            "type": typ,
            "retrieved": [
                {"company": x["company"], "section": x["section"], "page": x["page"],
                 "text": x["text"][:400]}
                for x in top
            ],
        })
        report_lines.append(f"\n{'='*70}\n【{typ}】{q}")
        for i, x in enumerate(top, 1):
            report_lines.append(f"  #{i} [{x['company']} {x['code']} | {x['section']} | p{x['page']}] score={x['score']}")
            report_lines.append(f"     {x['text'][:150]}")

    with open(os.path.join(DATA_DIR, "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "eval_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print("评测结果已存 eval_results.json / eval_report.txt")


if __name__ == "__main__":
    main()
