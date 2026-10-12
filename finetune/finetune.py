# -*- coding: utf-8 -*-
"""
方向B：用 LoRA 微调「董秘」+ 四格对照 + RAG 对照
在 Google Colab（T4 GPU）运行：!python finetune.py
需先上传：qa_train.json / four_grid.json / maotai_chunks.json（放本脚本同目录）
"""
import os
import json
import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                          TrainingArguments, Trainer, DataCollatorForSeq2Seq)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# ============ 配置 ============
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"   # 小模型（可换 0.5B 更快）
OUT_DIR = "./dongmi_lora"
TRAIN = "qa_train.json"
GRID = "four_grid.json"
CHUNKS = "maotai_chunks.json"

PROMPT_TMPL = "你是贵州茅台的董事会秘书（董秘），请用董秘口吻、简洁准确地回答投资者问题。\n投资者问：{q}\n董秘答：{a}"
RAG_TMPL = "你是贵州茅台的董事会秘书。请仅根据下面年报资料回答，若资料不足就说不清楚。\n资料：\n{ctx}\n投资者问：{q}\n董秘答："


def load_data():
    train = json.load(open(TRAIN, encoding="utf-8"))
    grid = json.load(open(GRID, encoding="utf-8"))
    return train, grid


def fmt(s):
    return PROMPT_TMPL.format(q=s["question"], a=s["answer"])


def train_model():
    train, _ = load_data()
    texts = [fmt(x) for x in train]

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16,
                             bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb,
                                                 device_map="auto", torch_dtype=torch.float16)
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    tok.pad_token = tok.eos_token
    model = prepare_model_for_kbit_training(model)

    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def tokenize(ex):
        out = tok(ex["text"], truncation=True, max_length=512, padding="max_length")
        out["labels"] = out["input_ids"].copy()
        return out

    ds = Dataset.from_dict({"text": texts}).map(tokenize, batched=True)

    args = TrainingArguments(output_dir=OUT_DIR, per_device_train_batch_size=2,
                             gradient_accumulation_steps=4, num_train_epochs=3,
                             learning_rate=2e-4, logging_steps=5, save_strategy="no",
                             fp16=True, report_to="none")
    trainer = Trainer(model=model, args=args, train_dataset=ds,
                      data_collator=DataCollatorForSeq2Seq(tok, padding=True))
    trainer.train()
    model.save_pretrained(OUT_DIR)
    tok.save_pretrained(OUT_DIR)
    print("✅ 微调完成，adapter 已存", OUT_DIR)
    return model, tok


def load_model(adapter=None):
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb,
                                                 device_map="auto", torch_dtype=torch.float16)
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    tok.pad_token = tok.eos_token
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
    return model, tok


def gen(model, tok, prompt, max_new=120):
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False,
                         temperature=None, top_p=None, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def four_grid_eval(model, tok):
    _, grid = load_data()
    results = {}
    for cell, items in grid.items():
        results[cell] = []
        for it in items:
            p = "你是贵州茅台的董事会秘书（董秘），请用董秘口吻简洁回答。\n投资者问：" + it["question"] + "\n董秘答："
            results[cell].append({"q": it["question"], "page": it.get("page"),
                                  "ref": it.get("answer", ""), "out": gen(model, tok, p)})
            print(f"  [{cell}] {it['question'][:30]}...", flush=True)
    json.dump(results, open("four_grid_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("✅ 四格结果已存 four_grid_results.json")
    return results


def rag_baseline(model, tok):
    """同一小模型 + 知识库（BM25 检索）对照"""
    from rank_bm25 import BM25Okapi
    import re
    chunks = json.load(open(CHUNKS, encoding="utf-8"))
    tokz = lambda s: [m.group() for m in re.finditer(r"[a-z0-9_]+|[一-鿿]", s.lower())]
    bm25 = BM25Okapi([tokz(c["text"]) for c in chunks])
    _, grid = load_data()
    results = {}
    for cell, items in grid.items():
        results[cell] = []
        for it in items:
            scores = bm25.get_scores(tokz(it["question"]))
            top = sorted(range(len(scores)), key=lambda i: -scores[i])[:3]
            ctx = "\n".join(f"[p{c['page']}] {c['text'][:200]}" for c in [chunks[i] for i in top])
            p = RAG_TMPL.format(ctx=ctx, q=it["question"])
            results[cell].append({"q": it["question"], "ref": it.get("answer", ""),
                                  "out": gen(model, tok, p)})
            print(f"  [RAG-{cell}] {it['question'][:30]}...", flush=True)
    json.dump(results, open("rag_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("✅ RAG 对照结果已存 rag_results.json")
    return results


if __name__ == "__main__":
    # 1. 微调（已在 Colab 跑过、adapter 存在则跳过）
    if os.path.exists(OUT_DIR):
        print("检测到已有 adapter，跳过微调，直接评测")
        model, tok = load_model(OUT_DIR)
    else:
        model, tok = train_model()

    # 2. 四格对照
    print("\n===== 四格对照 =====")
    four_grid_eval(model, tok)

    # 3. RAG 对照（同一小模型 + 知识库）
    print("\n===== RAG 对照（同一小模型）=====")
    rag_baseline(model, tok)
    print("\n全部完成")
