# -*- coding: utf-8 -*-
"""生成问答页截图：语义地图 + 回答 + 召回块（复刻 Streamlit 页面）"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from retrieval import Retriever
from answer import generate_answer

BASE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PALETTE = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#f4a261", "#6a4c93",
           "#118ab2", "#ef476f", "#06d6a0", "#073b4c", "#ffd166", "#9c89b8"]


def render(question, out_png):
    r = Retriever()
    coords = np.load(os.path.join(BASE, "data", "index", "umap_coords.npy"))
    companies = sorted({c["company"] for c in r.chunks})
    color = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(companies)}

    top = r.hybrid_search(question, top_k=5)
    idx = [x["idx"] for x in top]
    answer = generate_answer(question, top)

    q_vec = r.model.encode([question], normalize_embeddings=True)[0]
    sims = r.embeddings[idx] @ q_vec
    w = np.clip(sims, 0, None)
    q_coord = (coords[idx] * w[:, None]).sum(axis=0) / w.sum() if w.sum() > 0 else coords[idx].mean(axis=0)

    fig = plt.figure(figsize=(15, 8.5), dpi=130)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.05)

    # 左：语义地图
    ax = fig.add_subplot(gs[0])
    for comp in companies:
        m = np.array([i for i, c in enumerate(r.chunks) if c["company"] == comp])
        ax.scatter(coords[m, 0], coords[m, 1], s=3, c=color[comp], label=comp,
                   alpha=0.65, linewidths=0)
    ax.scatter(coords[idx, 0], coords[idx, 1], s=130, facecolors="none",
               edgecolors="#d90429", linewidths=2, label="召回块", zorder=5)
    ax.scatter([q_coord[0]], [q_coord[1]], marker="D", s=180, c="#ffd700",
               edgecolors="#b8860b", linewidths=1.5, label="问题", zorder=6)
    ax.set_title("语义地图（金色菱形=问题，红圈=召回块）", fontsize=13)
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="upper right", fontsize=8, ncol=2, framealpha=0.9)

    # 右：回答 + 召回块
    ax2 = fig.add_subplot(gs[1])
    ax2.axis("off")
    y = 1.0
    ax2.text(0.0, y, "" + question, fontsize=13, fontweight="bold", va="top", wrap=True)
    y -= 0.05
    ax2.text(0.0, y, "── 回答 ──", fontsize=11, fontweight="bold", color="#b0202e", va="top")
    y -= 0.035
    # 回答分块换行
    for line in _wrap(answer, 34):
        ax2.text(0.0, y, line, fontsize=10, va="top", wrap=True)
        y -= 0.026
    y -= 0.02
    ax2.text(0.0, y, "── 召回块（top5，带出处）──", fontsize=11, fontweight="bold", color="#b0202e", va="top")
    y -= 0.035
    for i, x in enumerate(top, 1):
        head = f"#{i} {x['company']} · {x['section']} · 第p{x['page']}"
        ax2.text(0.0, y, head, fontsize=9.5, fontweight="bold", color="#1f3a5f", va="top")
        y -= 0.022
        for line in _wrap(x["text"][:90], 38):
            ax2.text(0.02, y, line, fontsize=8.5, color="#444", va="top")
            y -= 0.02
        y -= 0.012
    ax2.set_xlim(0, 1); ax2.set_ylim(min(0, y - 0.05), 1.03)

    fig.suptitle("白酒行业年报问答知识库（12 家 · BM25+向量混合检索 · 答案带出处）",
                 fontsize=14, fontweight="bold", y=0.985)
    fig.savefig(out_png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成:", out_png)


def _wrap(text, n):
    return [text[i:i + n] for i in range(0, len(text), n)] or [""]


if __name__ == "__main__":
    render("贵州茅台2025年的毛利率是多少？", os.path.join(BASE, "页面截图_毛利率.png"))
    render("这12家白酒公司中，2025年净利润增速最快的是哪一家？", os.path.join(BASE, "页面截图_全景翻车.png"))
