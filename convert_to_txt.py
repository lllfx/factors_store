
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import glob
from bs4 import BeautifulSoup
CHROMEDRIVER_PATH = r"D:\software\chromedriver.exe"
OUT_HTML_ROOT = r"D:\UGit\factors_store\article_pages"
os.makedirs(OUT_HTML_ROOT, exist_ok=True)
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(
    service=Service(CHROMEDRIVER_PATH),
    options=options
)



try:
    for HTML_PATH in glob.glob(os.path.join(r"D:\UGit\factors_store\html_pages", "*.html")):
        file_url = "file:///" + os.path.abspath(HTML_PATH).replace("\\", "/")
        driver.get(file_url)

        wait = WebDriverWait(driver, 10)

        article = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "article.max-w-4xl")
            )
        )

        # ⭐ 删除“风险警告”块：div[role=alert]
        driver.execute_script("""
            const root = arguments[0];
            root.querySelectorAll('div[role="alert"]').forEach(el => el.remove());
          """, article)

        # ⭐ 删除 “Related Factors” 块：包含 h2 文本为 Related Factors 的 section
        driver.execute_script("""
            const root = arguments[0];
            root.querySelectorAll('section').forEach(sec => {
              const h2 = sec.querySelector('h2');
              if (h2 && h2.textContent.trim() === 'Related Factors') {
                sec.remove();
              }
            });
          """, article)

        # ⭐ 核心：拿完整 HTML 片段
        article_html = article.get_attribute("outerHTML")
        # soup = BeautifulSoup(article_html, "html.parser")
        #
        # # 格式化（带缩进）
        # pretty_html = soup.prettify()


        with open(os.path.join(OUT_HTML_ROOT,os.path.basename(HTML_PATH)), "w", encoding="utf-8") as f:
            f.write(article_html)

        print("保存完成:", os.path.join(OUT_HTML_ROOT,os.path.basename(HTML_PATH)))

finally:
    driver.quit()
