# -*- coding: utf-8 -*-
"""对正在运行的 04_app.py（Streamlit）做真实浏览器截屏（多题，逐题新开会话）：
提交题目后展开一个「页码出处」，截下 输入 + 实际回答 + 可展开的页码出处原文。"""
import os
import sys
import time
import base64

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "http://localhost:8501"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DRIVER = r"D:\xuke\work_dir\tmp_task\_drivers\chromedriver-win64\chromedriver.exe"
BASE = os.path.dirname(os.path.abspath(__file__))

QUESTIONS = [
    ("贵州茅台2025年的毛利率是多少？", "页面截图_真实网页_毛利率.png"),
    ("贵州茅台2025年营业收入是多少？", "页面截图_真实网页_茅台营收.png"),
    ("这12家白酒公司中，2025年净利润增速最快的是哪一家？", "页面截图_真实网页_全景翻车.png"),
]


def screenshot(driver, out_png):
    shot = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format": "png", "captureBeyondViewport": True, "fromSurface": True,
    })
    with open(out_png, "wb") as f:
        f.write(base64.b64decode(shot["data"]))
    return len(shot["data"])


def expand_first_source(driver):
    """展开第一个「页码出处」折叠块，露出原文。"""
    js = """
    var ex = document.querySelector('[data-testid="stExpander"]');
    if (!ex) return 'no-expander';
    var s = ex.querySelector('summary');
    if (s) { s.click(); return 'summary'; }
    var b = ex.querySelector('[role="button"]');
    if (b) { b.click(); return 'button'; }
    ex.click(); return 'container';
    """
    return driver.execute_script(js)


def capture_question(driver, question, out_png):
    driver.get(URL)  # 每题新开会话，输入框初始为空
    wait = WebDriverWait(driver, 240)
    inp = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[type="text"]')))
    time.sleep(1)
    inp.click()
    inp.send_keys(question)
    inp.send_keys(Keys.RETURN)

    end = time.time() + 240
    text = ""
    while time.time() < end:
        text = driver.execute_script("return document.body.innerText")
        if "页码出处" in text and "检索中" not in text and "生成回答" not in text:
            time.sleep(2)
            break
        time.sleep(1)

    r = expand_first_source(driver)
    time.sleep(2)

    size = screenshot(driver, out_png)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    ans_i = next((i for i, ln in enumerate(lines) if ln.startswith("📝 回答")), None)
    print(f"=== {os.path.basename(out_png)} ===")
    if ans_i is not None:
        print("回答:", lines[ans_i + 1] if ans_i + 1 < len(lines) else "(空)")
    print(f"展开首个出处: {r} | SAVED {out_png} | bytes={size}\n")
    return text


def main():
    opts = Options()
    opts.binary_location = CHROME
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1500,2600")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--force-device-scale-factor=1")
    opts.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(service=Service(DRIVER), options=opts)
    driver.set_page_load_timeout(180)
    try:
        print("开始逐题截屏（每题独立会话 + 展开一个出处）\n")
        for q, name in QUESTIONS:
            capture_question(driver, q, os.path.join(BASE, name))
        print("全部完成。")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
