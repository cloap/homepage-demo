# 白酒行业年报问答知识库（方向 A）

从巨潮资讯下载 12 家白酒上市公司 2025 年年度报告，提取文字 + 表格、按「公司/章节/页码」切块，构建 **BM25 + 向量** 混合索引，做检索式问答（答案带出处）。

## 目录结构

```
finance_qa/
├── 01_download.py    # 从 cninfo.com.cn 下载年报 PDF
├── 02_extract.py     # 提取文字+表格，按公司/章节/页码切块
├── 03_index.py       # 构建 BM25 + 向量索引
├── retrieval.py      # 混合检索（BM25 + 向量 RRF 融合）
├── 04_app.py         # Streamlit 问答页面
├── 05_eval.py        # 10 道题评测（含跨公司题）
├── 结论.md           # 一页结论
├── data/
│   ├── pdfs/         # 12 份年报 PDF
│   ├── chunks.json   # 5700 个切块
│   └── index/        # bm25.pkl + embeddings.npy
└── models/           # 本地嵌入模型（bge-small-zh-v1.5）
```

## 使用

```bash
# 1. 下载年报
python 01_download.py
# 2. 提取切块
python 02_extract.py
# 3. 建索引
python 03_index.py
# 4. 启动问答页
streamlit run 04_app.py
# 5. 跑评测
python 05_eval.py
```

## 技术栈

- 数据：巨潮资讯（cninfo.com.cn）12 家白酒公司 2025 年报
- 提取：PyMuPDF（文字 + `find_tables` 表格按行列还原）
- 切块：~700 字/块，带「公司、章节、页码」元信息
- 索引：BM25（rank_bm25）+ 向量（BAAI/bge-small-zh-v1.5，本地，512 维）
- 检索：混合检索 + RRF（Reciprocal Rank Fusion）融合
- 问答页：Streamlit

## 12 家公司

贵州茅台、五粮液、泸州老窖、山西汾酒、洋河股份、古井贡酒、今世缘、迎驾贡酒、舍得酒业、水井坊、口子窖、老白干酒
