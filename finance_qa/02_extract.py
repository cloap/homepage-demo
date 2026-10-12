# -*- coding: utf-8 -*-
"""提取 12 份年报的文字 + 表格，按「公司/章节/页码/块序号」切块（对齐第三课 PPT 第25页）
规格：800 字一块、重合 120 字、句末收尾；每块带四个标签（公司、章节、页码、块序号）。
表格按行还原后独立成块，行列结构不破坏。
"""
import os
import re
import json
import fitz

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")

SECTION_RE = re.compile(r'^第[一二三四五六七八九十百]+[节章]\s*[^\n]{0,30}')

CHUNK_SIZE = 800   # 每块约 800 字（对齐 PPT）
OVERLAP = 120      # 相邻块重合 120 字


def split_sentences(text):
    """按句号/换行切分，便于拼块"""
    parts = re.split(r'(?<=[。；;.!?])\s*|\n+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text, meta):
    """把一段文字切成若干块：800 字/块、重合 120 字、尽量在句末收尾"""
    chunks = []
    sents = split_sentences(text)
    buf = []
    buf_len = 0
    for sent in sents:
        buf.append(sent)
        buf_len += len(sent)
        if buf_len >= CHUNK_SIZE:
            chunks.append({**meta, "text": " ".join(buf)})
            # 保留末尾 ~120 字作为重合
            carry = []
            carry_len = 0
            while buf and carry_len < OVERLAP:
                s = buf.pop()
                carry.append(s)
                carry_len += len(s)
            carry.reverse()
            buf = carry
            buf_len = carry_len
    if buf:
        chunks.append({**meta, "text": " ".join(buf)})
    return chunks


def extract_pdf(pdf_path, name, code):
    doc = fitz.open(pdf_path)
    chunks = []
    idx = 0
    cur_section = "卷首/目录"
    for pno in range(len(doc)):
        page = doc[pno]
        text = page.get_text()

        # 检测章节标题（在本页中查找）
        lines = text.split("\n")
        page_section = None
        for ln in lines:
            ln = ln.strip()
            if SECTION_RE.match(ln) and len(ln) <= 30:
                page_section = ln
                break

        meta = {"company": name, "code": code, "section": cur_section, "page": pno + 1}

        # 表格：find_tables 还原为「行 | 列」，独立成块（行列结构保留）
        try:
            for tbl in page.find_tables():
                rows = tbl.extract()
                if not rows:
                    continue
                md = []
                for r in rows[:60]:
                    cells = [("" if c is None else str(c).replace("\n", " ").strip()) for c in r]
                    md.append(" | ".join(cells))
                if md:
                    chunks.append({**meta, "idx": idx, "text": "[表格]\n" + "\n".join(md)})
                    idx += 1
        except Exception:
            pass

        # 正文切块
        for c in chunk_text(text, meta):
            chunks.append({**c, "idx": idx})
            idx += 1

        if page_section:
            cur_section = page_section

    doc.close()
    return chunks


def main():
    with open(os.path.join(DATA_DIR, "meta.json"), encoding="utf-8") as f:
        meta = json.load(f)

    all_chunks = []
    for m in meta:
        pdf = os.path.join(PDF_DIR, m["file"])
        name, code = m["name"], m["code"]
        chunks = extract_pdf(pdf, name, code)
        all_chunks.extend(chunks)
        print(f"{name}: {len(chunks)} 块")

    with open(os.path.join(DATA_DIR, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=1)

    print(f"\n总计 {len(all_chunks)} 块，已存 chunks.json")
    # 统计
    secs = {}
    for c in all_chunks:
        secs[c["section"]] = secs.get(c["section"], 0) + 1
    print("章节分布(前15):")
    for s, n in sorted(secs.items(), key=lambda x: -x[1])[:15]:
        print(f"  {s}: {n}")


if __name__ == "__main__":
    main()
