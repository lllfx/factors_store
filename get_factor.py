import re
import json
from typing import Any, Dict, Optional

def js_string_unescape_min(s: str) -> str:
    """
    最小化反转义：只处理 Next.js 这类 script 字符串里常见的转义，
    避免 unicode_escape 把中文弄乱码。
    """
    # 顺序很重要：先还原 \\ 再处理其他会用到反斜杠的转义会出问题
    s = s.replace(r"\\", "\\")
    s = s.replace(r"\/", "/")
    s = s.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t")
    s = s.replace(r"\"", '"')
    return s

def extract_balanced_object(text: str, key: str) -> Optional[str]:
    """
    从 text 中找到 '"<key>":{...}' 的 { ... }，用括号深度配对返回 JSON 文本。
    """
    idx = text.find(f'"{key}":')
    if idx == -1:
        return None
    brace_start = text.find("{", idx)
    if brace_start == -1:
        return None

    depth = 0
    for i in range(brace_start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start : i + 1]
    return None

def parse_factor(html: str) -> Dict[str, Optional[str]]:
    """
    解析因子：id / name(title) / explanation / description
    """
    out = {
        "id": None,
        "name": None,
        "title": None,
        "explanation": None,
        "description": None,
    }

    # 1) 优先：抓 Next.js 的 self.__next_f.push([1,"6:..."]) 那段
    m = re.search(r'self\.__next_f\.push\(\[1,"6:(.*?)"\]\)\s*</script>', html, flags=re.S)
    if m:
        payload = m.group(1)
        payload = js_string_unescape_min(payload)

        factor_obj_text = extract_balanced_object(payload, "factor")
        if factor_obj_text:
            factor = json.loads(factor_obj_text)
            out["id"] = factor.get("id")
            out["name"] = factor.get("name")
            out["title"] = factor.get("title")
            out["explanation"] = factor.get("explanation")
            out["description"] = factor.get("description")
            return out

    # 2) 兜底：h1 + canonical 里解析
    h1 = re.search(r"<h1[^>]*>\s*([^<]+?)\s*</h1>", html)
    if h1:
        out["name"] = h1.group(1).strip()

    canon = re.search(
        r'<link[^>]+rel="canonical"[^>]+href="https://factors\.directory/zh/factors/[^/]+/([^"]+)"',
        html
    )
    if canon:
        out["id"] = canon.group(1)

    return out

if __name__ == "__main__":
    # 方式1：从文件读（推荐）
    html = open("page.txt", "r", encoding="utf-8").read()

    info = parse_factor(html)
    print(json.dumps(info, ensure_ascii=False, indent=2))
