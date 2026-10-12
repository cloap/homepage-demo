# -*- coding: utf-8 -*-
"""答案生成：用 DeepSeek（Anthropic 兼容端点）基于召回块生成带出处的回答"""
import os
import json
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))


def load_env():
    env = {}
    p = os.path.join(BASE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


_ENV = load_env()


def deepseek_chat(messages, max_tokens=800, model=None):
    """调用 DeepSeek Anthropic 兼容 Messages API，返回文本"""
    token = _ENV.get("DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))
    base = _ENV.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic")
    model = model or _ENV.get("DEEPSEEK_MODEL", "deepseek-chat")
    url = base.rstrip("/") + "/v1/messages"
    body = json.dumps({"model": model, "max_tokens": max_tokens, "messages": messages}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "x-api-key": token, "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    r = urllib.request.urlopen(req, timeout=180)
    data = json.loads(r.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def fmt_chunk(idx, c):
    return (f"[{idx}] 【{c['company']}｜{c['section']}｜p{c['page']}】 {c['text']}")


def generate_answer(question, chunks, max_tokens=800):
    """基于召回块生成带出处的回答"""
    if not chunks:
        return "（未召回任何材料，无法回答）"
    evidence = "\n\n".join(fmt_chunk(i, c) for i, c in enumerate(chunks, 1))
    sys = ("你是财报问答助手。只依据下面给的年报片段回答，关键数字/结论后标注出处【公司 p页码】。"
           "如果片段不足，明确说『材料未覆盖』，不要编造。")
    user = f"问题：{question}\n\n年报片段：\n{evidence}\n\n请回答（一句话结论 + 关键数字带出处）："
    return deepseek_chat([
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ], max_tokens=max_tokens)


def extract_metric(question, chunks, max_tokens=300):
    """从片段中抽取单个指标数值（用于跨公司逐家取证）"""
    evidence = "\n".join(fmt_chunk(i, c) for i, c in enumerate(chunks, 1))
    user = (f"从下面片段抽取目标指标的数值，只输出『公司: 数值 (单位)』，找不到就输出『未覆盖』。\n"
            f"目标：{question}\n\n{evidence}")
    return deepseek_chat([
        {"role": "user", "content": user},
    ], max_tokens=max_tokens).strip()


if __name__ == "__main__":
    # 自测
    print(deepseek_chat([{"role": "user", "content": "回复『OK』两个字"}], max_tokens=10))
