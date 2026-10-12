# -*- coding: utf-8 -*-
"""提取 12 份年报的文字 + 表格，按「公司/章节/页码」切块"""
import os
import re
import json
import fitz

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")

SECTION_RE = re.compile(r'^第[一二三四五六七八九十百]+[节章]\s*[^\n]{0,30}')

CHUNK_SIZE = 700   # 每块约 700 字符


def split_sentences(text):
    """按句号/换行切分，便于拼块"""
    parts = re.split(r'(?<=[。；;.!?])\s*|\n+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text, meta):
    """把一段文字切成若干块，每块带 meta"""
    chunks = []
    buf = []
    buf_len = 0
    for sent in split_sentences(text):
        buf.append(sent)
        buf_len += len(sent)
        if buf_len >= CHUNK_SIZE:
            chunks.append({**meta, "text": " ".join(buf)})
            buf = []
            buf_len = 0
    if buf:
        chunks.append({**meta, "text": " ".join(buf)})
    return chunks


def extract_pdf(pdf_path, name, code):
    doc = fitz.open(pdf_path)
    chunks = []
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

        # 表格：find_tables 还原为「行 | 列」，每个表格独立成块（不被正文切块打断/截断）
        try:
            for tbl in page.find_tables():
                rows = tbl.extract()
                if not rows:
                    continue
                md = []
                for r in rows[:60]:  # 限制行数
                    cells = [("" if c is None else str(c).replace("\n", " ").strip()) for c in r]
                    md.append(" | ".join(cells))
                if md:
                    # 每个表格一块，行列结构完整保留
                    chunks.append({**meta, "text": "[表格]\n" + "\n".join(md)})
        except Exception:
            pass

        # 正文单独切块
        chunks.extend(chunk_text(text, meta))

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
