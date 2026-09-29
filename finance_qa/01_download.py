# -*- coding: utf-8 -*-
"""从巨潮资讯下载 12 家白酒公司 2025 年年度报告 PDF"""
import os
import json
import time
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# (股票代码, orgId, 市场column, 公司名)
COMPANIES = [
    ("600519", "gssh0600519", "sse", "贵州茅台"),
    ("000858", "gssz0000858", "szse", "五粮液"),
    ("000568", "gssz0000568", "szse", "泸州老窖"),
    ("600809", "gssh0600809", "sse", "山西汾酒"),
    ("002304", "gssz0002304", "szse", "洋河股份"),
    ("000596", "gssz0000596", "szse", "古井贡酒"),
    ("603369", "gssh0603369", "sse", "今世缘"),
    ("603198", "gssh0603198", "sse", "迎驾贡酒"),
    ("600702", "gssh0600702", "sse", "舍得酒业"),
    ("600779", "gssh0600779", "sse", "水井坊"),
    ("603589", "gssh0603589", "sse", "口子窖"),
    ("600559", "gssh0600559", "sse", "老白干酒"),
]

QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
    "X-Requested-With": "XMLHttpRequest",
}


def find_annual_report(code, orgid, column):
    """查询某公司年度报告，返回中文版年报的 adjunctUrl"""
    data = {
        "pageNum": 1, "pageSize": 30, "column": column, "tabName": "fulltext",
        "plate": "", "stock": f"{code},{orgid}", "searchkey": "", "secid": "",
        "category": "category_ndbg_szsh", "trade": "",
        "seDate": "2026-01-01~2026-12-31", "sortName": "", "sortType": "",
        "isHLtitle": "true",
    }
    r = requests.post(QUERY_URL, data=data, headers=HEADERS, timeout=30)
    anns = (r.json().get("announcements") or [])
    # 过滤：中文版、非摘要、非已取消
    for a in anns:
        title = a.get("announcementTitle", "")
        url = a.get("adjunctUrl", "")
        if "年度报告" in title and "英文" not in title and "摘要" not in title and "已取消" not in title:
            if url:
                return title, url
    return None, None


def download(url, out_path):
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://static.cninfo.com.cn" + url
    elif not url.startswith("http"):
        url = "https://static.cninfo.com.cn/" + url
    r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)
    return len(r.content)


def main():
    meta = []
    for code, orgid, column, name in COMPANIES:
        out = os.path.join(PDF_DIR, f"{name}_{code}.pdf")
        if os.path.exists(out) and os.path.getsize(out) > 100000:
            print(f"[跳过] {name} 已存在")
            meta.append({"name": name, "code": code, "file": os.path.basename(out)})
            continue
        try:
            title, url = find_annual_report(code, orgid, column)
            if not url:
                print(f"[失败] {name} 未找到年报")
                continue
            size = download(url, out)
            print(f"[成功] {name} <- {title} ({size//1024} KB)")
            meta.append({"name": name, "code": code, "file": os.path.basename(out), "title": title})
        except Exception as e:
            print(f"[错误] {name}: {e}")
        time.sleep(1)

    with open(os.path.join(DATA_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\n共下载 {len(meta)} 份，元信息已存 meta.json")


if __name__ == "__main__":
    main()
