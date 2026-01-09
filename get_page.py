import csv
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE = "https://factors.directory"

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")

service = Service(executable_path=r"D:\software\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 12)

driver.get("https://factors.directory/zh/factors/tech/price-volume-divergence")

# 等左侧/页面内容加载出来
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(2)

def norm_url(href: str) -> str:
    if not href:
        return ""
    # 页面里多为相对路径：/zh/factors/...
    return urljoin(BASE, href)

def get_category_buttons():
    """
    找分类按钮：button 内有 span（分类名），且样式像左侧菜单按钮
    """
    # 你给的 button class 里有 w-full / flex / rounded-xl，很典型
    return driver.find_elements(
        By.XPATH,
        "//button[contains(@class,'w-full') and contains(@class,'rounded') and .//span]"
    )

def get_current_links():
    """
    抓当前展开区域里的 a（名称 + href）
    尽量过滤掉导航/页脚等无关链接：要求 href 里包含 /zh/factors/
    """
    links = driver.find_elements(By.XPATH, "//a[contains(@href, '/zh/factors/')]")
    out = []
    for a in links:
        name = a.text.strip()
        href = a.get_attribute("href") or a.get_attribute("href")  # 保险写法
        href = norm_url(href)
        if name and href:
            out.append((name, href))
    # 去重（同一分类里可能重复渲染）
    dedup = []
    seen = set()
    for name, href in out:
        key = (name, href)
        if key not in seen:
            seen.add(key)
            dedup.append((name, href))
    return dedup

results = []  # [{'category':..., 'name':..., 'url':...}, ...]

buttons = get_category_buttons()
print("分类按钮数量:", len(buttons))
seen_name_url = set()   # ⭐ 新增：全局去重
for i in range(len(buttons)):
    # ⚠️ 每次循环都重新抓按钮，避免 stale
    buttons = get_category_buttons()
    if i >= len(buttons):
        break

    btn = buttons[i]
    category = btn.text.strip().splitlines()[0].strip() if btn.text.strip() else f"cat_{i}"
    print(f"\n=== [{i+1}/{len(buttons)}] 点击分类: {category} ===")

    # 滚动到可见位置
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.3)

    # 点击（JS click 最稳）
    try:
        driver.execute_script("arguments[0].click();", btn)
    except Exception as e:
        print("点击失败，尝试普通 click：", e)
        try:
            btn.click()
        except Exception as e2:
            print("仍失败，跳过该分类：", e2)
            continue

    # 等待该分类下的链接出现（给一点时间让列表渲染）
    # 这里不强依赖“必须出现新链接”，避免某些分类为空导致卡死
    time.sleep(1.2)

    links = get_current_links()
    print(f"抓到链接数: {len(links)}")

    for name, url in links:
        key = (name, url)

        # ⭐ 去重：name + url 都相同则跳过
        if key in seen_name_url:
            continue

        seen_name_url.add(key)

        results.append({
            "category": category,
            "name": name,
            "url": url
        })
        results.append({"category": category, "name": name, "url": url})

# 全局去重（不同分类可能出现同一因子链接；你也可以保留重复）
final = []
seen = set()
for row in results:
    key = (row["category"], row["name"], row["url"])
    if key not in seen:
        seen.add(key)
        final.append(row)

# 保存 CSV
out_path = "factors_links.csv"
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["category", "name", "url"])
    w.writeheader()
    w.writerows(final)

print("\n保存完成:", out_path)
print("总记录数:", len(final))

driver.quit()
