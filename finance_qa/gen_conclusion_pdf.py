# -*- coding: utf-8 -*-
"""生成一页结论 PDF"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCX = r"D:\xuke\work_dir\tmp_task\finance_qa\一页结论.docx"
PDF = r"D:\xuke\work_dir\tmp_task\finance_qa\一页结论.pdf"

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Microsoft YaHei"
normal.font.size = Pt(10.5)
normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Microsoft YaHei")
for s in doc.sections:
    s.top_margin = Inches(0.7)
    s.bottom_margin = Inches(0.7)
    s.left_margin = Inches(0.9)
    s.right_margin = Inches(0.9)


def title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)


def heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0xB0, 0x20, 0x2E)


def body(text, bold=False, indent=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    if indent:
        p.paragraph_format.left_indent = Inches(0.25)
    r = p.add_run(text)
    r.bold = bold


title("方向 A · 一页结论")
body("白酒行业年报问答知识库 —— 同一批财报，什么问题该建库，什么问题该微调", bold=True)

heading("核心结论")
body("同一批财报，单公司事实/指标查找题适合检索式建库（答得准），跨公司全景/对比题翻车（答不了）。"
     "原因：按公司切块的索引只支持「定位」，不支持「跨公司聚合、对齐口径、排序」。")

heading("哪类题答得好：单公司事实 / 治理 / 分红 / 财务（5/7 答对）")
body("• 茅台营收 16,883,810.25 万元（p54）、五粮液归母净利 89.54 亿（p7）", indent=1)
body("• 茅台毛利率 91.23%（p10）、洋河每10股派14.70元（p40）、汾酒实控人（p43）", indent=1)
body("为什么好：答案集中在一家公司某个章节/一张表；表格按行列独立成块后，毛利率、分红、归母净利这类「藏在表格里」的精确数值也能抽出。", indent=1)

heading("哪类题翻车：跨公司全景 / 对比（2/3 翻车）")
body("• 「12家净利增速最快」「茅台vs五粮液谁营收更高」→ 材料未覆盖，无法排序/比较", indent=1)
body("• 「12家营收最大」→ 各家口径不齐，不敢下结论", indent=1)
body("为什么翻车：「谁最大/最快」需先把 12 家指标抽出、对齐口径、再排序/相减，这是聚合不是检索；「增速」是派生指标，各公司披露位置/口径不一致，逐家取证也抓不准。", indent=1)

heading("一句话结论")
body("同一批财报，「单公司指标查找」适合建库（检索式）；「跨公司全局比较/增速排序」不适合——"
     "后者需先解析出对齐口径的结构化财务表再聚合，或交给生成式 LLM 做多块综合（方向 B 微调的用武之地）。", bold=True)

heading("附：10 题结果速览")
body("✅ 答对 5 题（单公司事实/治理/分红/财务）｜⚠️ 部分 3 题（需计算/口径不齐/过于保守）｜❌ 翻车 2 题（跨公司全景/对比）")

doc.save(DOCX)

# 转 PDF
import win32com.client
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    d = word.Documents.Open(DOCX, ReadOnly=True)
    d.SaveAs(PDF, FileFormat=17)
    d.Close(False)
finally:
    word.Quit()
print("已生成:", PDF)
