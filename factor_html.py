import csv
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CSV_PATH = "factors_links.csv"          # 你的三列：category,name,url
OUT_DIR = "html_pages"                 # 输出目录
CHROMEDRIVER_PATH = r"D:\software\chromedriver.exe"

os.makedirs(OUT_DIR, exist_ok=True)


def safe_filename(s: str, max_len: int = 120) -> str:
    """
    Windows 安全文件名：去掉非法字符、压缩空白、截断长度
    """
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", s)  # 非法字符替换
    s = s.rstrip(". ")  # 末尾不能是点/空格（Windows）
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s or "untitled"


options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
# 如果你想无头模式，取消下一行注释
# options.add_argument("--headless=new")

service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

def save_html(category: str, name: str, url: str):
    filename = f"{safe_filename(category)}_{safe_filename(name)}.html"
    path = os.path.join(OUT_DIR, filename)
    if os.path.exists(path):
        print(f"已存在: {path}")
        return path


    driver.get(url)

    # 等页面主内容加载：至少等 body 出来，再额外等一下渲染
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(1.5)

    html = driver.page_source
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path

try:
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print("待抓取数量:", len(rows))

    for i, row in enumerate(rows, start=1):
        category = (row.get("category") or "").strip()
        name = (row.get("name") or "").strip()
        url = (row.get("url") or "").strip()

        if not (category and name and url):
            print(f"[{i}] 跳过：字段缺失 -> {row}")
            continue

        print(f"[{i}/{len(rows)}] 访问: {name} -> {url}")
        try:
            saved_path = save_html(category, name, url)
            print("    保存:", saved_path)
        except Exception as e:
            print("    失败:", e)

finally:
    driver.quit()
    print("完成。")
