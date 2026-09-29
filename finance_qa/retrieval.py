# -*- coding: utf-8 -*-
"""混合检索：BM25 + 向量（RRF 融合），答案带出处"""
import os
import re
import json
import glob
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
INDEX_DIR = os.path.join(DATA_DIR, "index")
HF_MODEL = "BAAI/bge-small-zh-v1.5"


def _find_local_model():
    """优先用本地已下载的模型（ModelScope 缓存），否则云端从 HF 下载"""
    for p in glob.glob(os.path.join(BASE, "models", "**", "snapshots", "master"), recursive=True):
        if os.path.isdir(p):
            return p
    return None


def tokenize(text):
    text = text.lower()
    return [m.group() for m in re.finditer(r'[a-z0-9_]+|[一-鿿]', text)]


class Retriever:
    def __init__(self):
        with open(os.path.join(INDEX_DIR, "chunks.json"), encoding="utf-8") as f:
            self.chunks = json.load(f)
        with open(os.path.join(INDEX_DIR, "bm25.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
        self.embeddings = np.load(os.path.join(INDEX_DIR, "embeddings.npy"))
        local = _find_local_model()
        self.model = SentenceTransformer(local if local else HF_MODEL, device="cpu")

    def hybrid_search(self, query, top_k=5):
        q_tokens = tokenize(query)
        bm25_scores = self.bm25.get_scores(q_tokens)
        q_vec = self.model.encode([query], normalize_embeddings=True)[0]
        cos_scores = self.embeddings @ q_vec

        bm25_top = np.argsort(-bm25_scores)[:top_k * 2]
        vec_top = np.argsort(-cos_scores)[:top_k * 2]

        rrf = {}
        for rank, idx in enumerate(bm25_top):
            rrf[idx] = rrf.get(idx, 0) + 1.0 / (rank + 60)
        for rank, idx in enumerate(vec_top):
            rrf[idx] = rrf.get(idx, 0) + 1.0 / (rank + 60)

        sorted_idx = sorted(rrf.keys(), key=lambda i: -rrf[i])[:top_k]
        results = []
        for i in sorted_idx:
            results.append({
                "idx": i,
                "company": self.chunks[i]["company"],
                "code": self.chunks[i]["code"],
                "section": self.chunks[i]["section"],
                "page": self.chunks[i]["page"],
                "text": self.chunks[i]["text"],
                "score": round(float(rrf[i]), 4),
                "bm25": round(float(bm25_scores[i]), 2),
                "cos": round(float(cos_scores[i]), 4),
            })
        return results


if __name__ == "__main__":
    r = Retriever()
    for q in ["贵州茅台2025年营业收入是多少", "五粮液和泸州老窖的净利润对比"]:
        print(f"\n【问】{q}")
        for res in r.hybrid_search(q, top_k=3):
            print(f"  [{res['company']} {res['code']} | {res['section']} p{res['page']} | score={res['score']}]")
            print(f"    {res['text'][:80]}...")
