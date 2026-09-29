# -*- coding: utf-8 -*-
"""构建 BM25 + 向量索引"""
import os
import json
import re
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INDEX_DIR = os.path.join(DATA_DIR, "index")
os.makedirs(INDEX_DIR, exist_ok=True)

MODEL_PATH = r"D:\xuke\work_dir\tmp_task\finance_qa\models\models\AI-ModelScope--bge-small-zh-v1.5\snapshots\master"


def tokenize(text):
    """中文按字切分 + 英文/数字按词保留"""
    text = text.lower()
    tokens = []
    for m in re.finditer(r'[a-z0-9_]+|[\u4e00-\u9fff]', text):
        tokens.append(m.group())
    return tokens


def main():
    with open(os.path.join(DATA_DIR, "chunks.json"), encoding="utf-8") as f:
        chunks = json.load(f)
    texts = [c["text"] for c in chunks]
    print(f"共 {len(chunks)} 块")

    # 1. BM25 索引
    tokenized = [tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized)
    with open(os.path.join(INDEX_DIR, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    print("BM25 索引完成")

    # 2. 向量索引
    model = SentenceTransformer(MODEL_PATH, device="cpu")
    embeddings = model.encode(texts, batch_size=32, normalize_embeddings=True,
                              show_progress_bar=True)
    np.save(os.path.join(INDEX_DIR, "embeddings.npy"), embeddings)
    print(f"向量索引完成，形状 {embeddings.shape}")

    # 保存 chunks（和索引对齐）
    with open(os.path.join(INDEX_DIR, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=1)

    print("索引全部保存到", INDEX_DIR)


if __name__ == "__main__":
    main()
