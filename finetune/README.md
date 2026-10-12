# 方向 B · 用 LoRA 微调「董秘」+ 四格对照 + RAG 对照

选贵州茅台一家公司，从 2025 年报生成「投资者问 → 董秘答」问答对，在 Colab 上用 QLoRA 微调 Qwen2.5-1.5B，做四格对照（训练过/没见过 × 原问法/换问法），再和「同一小模型 + 知识库」对比，讨论**记忆 vs 泛化**。

## 目录

```
finetune/
├── 01_generate_data.py   # 用 DeepSeek 从茅台年报生成问答对（答案注明页码）
├── 02_spotcheck.py       # 人工抽检：核对答案数字是否在原文，删编造
├── finetune.py           # Colab 训练脚本：QLoRA 微调 + 四格 + RAG 对照
├── finetune_colab.ipynb  # Colab 笔记本
├── data/
│   ├── qa_train.json     # 训练集 38 对（抽检后）
│   ├── qa_test.json      # 未见过题 10 对
│   ├── four_grid.json    # 四格题（10×4）
│   ├── maotai_chunks.json# 茅台年报切块（RAG 对照用）
│   └── spotcheck.md      # 抽检记录
└── 结论.md               # 一页结论（记忆 vs 泛化）
```

## 流程

1. **生成数据**（本机）：`python 01_generate_data.py` → 用 DeepSeek 从 549 个茅台切块生成 50 对问答（答案带页码）
2. **人工抽检**（本机）：`python 02_spotcheck.py` → 核对答案数字是否在原文，抓到 2 对编造（"5.95亿""650.33亿"）已删除，保留 38 对
3. **微调**（Colab）：上传 `finetune.py` + 3 个 json，运行 `finetune_colab.ipynb` → QLoRA 微调 Qwen2.5-1.5B（3 epoch）
4. **四格对照**：训练过/没见过 × 原问法/换问法，各 10 题，输出 `four_grid_results.json`
5. **RAG 对照**：同一小模型 + BM25 检索茅台切块，答同一批题，输出 `rag_results.json`

## 四格设计

| | 原问法 | 换问法 |
|---|---|---|
| **训练见过** | 训练集里出现过的问题 | 同题换说法 |
| **没训练过** | 未训练过的茅台事实 | 同题换说法 |

- 训练见过×原问法 答对 → 是**记忆**（背下来了）
- 训练见过×换问法 仍答对 → 有**泛化**（理解而非死背）
- 没训练过 答错/编造 → 微调没有**新知识**，只会套格式

## 依赖（Colab 自动装）

`transformers peft bitsandbytes datasets accelerate rank-bm25`
