# -*- coding: utf-8 -*-
"""白酒年报问答页（Streamlit）：语义地图 + 检索式问答（答案带出处）"""
import os
import json
import pickle
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from retrieval import Retriever

st.set_page_config(page_title="白酒年报问答", page_icon="🍶", layout="wide")

BASE = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(BASE, "data", "index")

PALETTE = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#f4a261", "#6a4c93",
           "#118ab2", "#ef476f", "#06d6a0", "#073b4c", "#ffd166", "#9c89b8"]


@st.cache_resource
def load_all():
    r = Retriever()
    coords = np.load(os.path.join(INDEX_DIR, "umap_coords.npy"))
    return r, coords


retriever, coords = load_all()
companies = sorted({c["company"] for c in retriever.chunks})
color_map = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(companies)}


def build_map(highlight_idx=None, q_coord=None):
    """画语义地图：每家公司一个颜色，高亮召回块，问题用金色菱形"""
    fig = go.Figure()
    for comp in companies:
        idx = [i for i, c in enumerate(retriever.chunks) if c["company"] == comp]
        idx = np.array(idx)
        fig.add_trace(go.Scattergl(
            x=coords[idx, 0], y=coords[idx, 1], mode="markers", name=comp,
            marker=dict(size=4, color=color_map[comp], opacity=0.7),
            text=[f"{retriever.chunks[i]['section']} p{retriever.chunks[i]['page']}" for i in idx],
            hoverinfo="text",
        ))
    if highlight_idx:
        hi = np.array(highlight_idx)
        fig.add_trace(go.Scattergl(
            x=coords[hi, 0], y=coords[hi, 1], mode="markers", name="召回块",
            marker=dict(size=12, color="#d90429", opacity=1, symbol="circle",
                        line=dict(color="white", width=1)),
            text=[f"{retriever.chunks[i]['company']} {retriever.chunks[i]['section']} p{retriever.chunks[i]['page']}" for i in hi],
            hoverinfo="text",
        ))
    if q_coord is not None:
        fig.add_trace(go.Scattergl(
            x=[q_coord[0]], y=[q_coord[1]], mode="markers", name="问题",
            marker=dict(size=18, color="#ffd700", symbol="diamond",
                        line=dict(color="#b8860b", width=2)),
        ))
    fig.update_layout(
        height=520, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(font=dict(size=11)), hovermode="closest",
    )
    return fig


st.title("🍶 白酒行业年报问答知识库")
st.caption("12 家白酒上市公司 2025 年报 · BM25 + 向量混合检索 · 答案带出处 · 语义地图")

query = st.text_input("🔍 提问", placeholder="例如：贵州茅台2025年营业收入是多少？")
top_k = st.slider("返回结果数", 1, 10, 5)

if query:
    with st.spinner("检索中…"):
        results = retriever.hybrid_search(query, top_k=top_k)
        chunk_idx = [r["idx"] for r in results]
        # 问题位置 = 召回块 2D 坐标的相似度加权质心
        q_vec = retriever.model.encode([query], normalize_embeddings=True)[0]
        sims = retriever.embeddings[chunk_idx] @ q_vec
        weights = np.clip(sims, 0, None)
        if weights.sum() > 0:
            q_coord = (coords[chunk_idx] * weights[:, None]).sum(axis=0) / weights.sum()
        else:
            q_coord = coords[chunk_idx].mean(axis=0)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("#### 语义地图（金色菱形 = 问题，红色 = 召回块）")
        st.plotly_chart(build_map(highlight_idx=chunk_idx, q_coord=q_coord), use_container_width=True)
    with col2:
        st.markdown(f"#### 检索结果（{len(results)} 块）")
        for i, r in enumerate(results, 1):
            with st.container(border=True):
                st.markdown(f"**#{i}** 🏢 {r['company']}（{r['code']}）· {r['section']} · 📍第{r['page']}页")
                st.write(r["text"])
                st.caption(f"得分 {r['score']}｜BM25 {r['bm25']}｜向量 {r['cos']}")

st.divider()
st.caption("数据：巨潮资讯网 2025 年报 · 模型 BAAI/bge-small-zh-v1.5（本地）")
