# 白酒行业年报问答知识库（方向 A）

从巨潮资讯下载 12 家白酒上市公司 2025 年年度报告，提取文字 + 表格（按行列还原）、按「公司/章节/页码」切块，构建 **BM25 + 向量** 混合索引，做检索式问答——**答案带出处**，并对 10 道题逐题评测（召回与答案分开评价）。

## 目录结构

```
finance_qa/
├── 01_download.py      # 从 cninfo.com.cn 下载年报 PDF
├── 02_extract.py       # 提取文字+表格；表格独立成块、行列还原；带公司/章节/页码
├── 03_index.py         # BM25 + 向量索引 + UMAP 语义地图
├── retrieval.py        # 混合检索（BM25 + 向量 RRF 融合）
├── answer.py           # 基于召回块生成带出处回答（DeepSeek，Anthropic 兼容端点）
├── 04_app.py           # Streamlit 问答页面（语义地图 + 回答 + 召回块）
├── 05_eval.py          # 10 道题评测
├── 来源清单.md         # 12 家公司官方年报来源链接：召回 + 实际回答（跨公司题逐家取证）
├── gen_screenshot.py   # 生成问答页截图
├── gen_conclusion_pdf.py  # 生成一页结论 PDF
├── 评测记录.md         # 10 题逐题记录（召回块 + 实际回答 + 判定）
├── 结论.md             # 一页结论
├── data/               # pdfs/ + chunks.json + index/（本地，不入仓库）
└── models/             # 本地嵌入模型 bge-small-zh-v1.5（不入仓库）
```

## 使用

```bash
# 1. 下载年报
python 01_download.py
# 2. 提取切块（表格行列还原）
python 02_extract.py
# 3. 建索引（BM25 + 向量 + UMAP）
python 03_index.py
# 4. 启动问答页
streamlit run 04_app.py
# 5. 跑 10 题评测（召回 + 实际回答）
python 05_eval.py
```

> 回答生成需要 DeepSeek key：放在 `.env`（`DEEPSEEK_API_KEY`），已写入 `.gitignore`。

## 技术栈

- 数据：巨潮资讯（cninfo.com.cn）12 家白酒公司 2025 年报
- 提取：PyMuPDF（文字 + `find_tables` 表格按行列还原，独立成块）
- 切块：正文 800 字/块、重合 120 字，带「公司、章节、页码、块序号」四标签
- 索引：BM25（rank_bm25）+ 向量（BAAI/bge-small-zh-v1.5，512 维，向量化拼入公司名+章节名）+ UMAP 语义地图
- 检索：混合检索 + RRF 融合
- 回答：DeepSeek（Anthropic 兼容 Messages API），答案带出处
- 评测：召回与答案分开评价，跨公司题逐家取证

## 12 家公司

贵州茅台、五粮液、泸州老窖、山西汾酒、洋河股份、古井贡酒、今世缘、迎驾贡酒、舍得酒业、水井坊、口子窖、老白干酒
