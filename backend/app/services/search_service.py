import re
import urllib.parse
import httpx
import time
import random
from app.core.config import settings
from app.services.groq_client import call_groq

def should_search_for_factcheck(user_argument: str) -> bool:
    """Detect if the user argument contains statistics, years, or potential citations."""
    text = (user_argument or "").lower().strip()
    if not text:
        return False
        
    # Look for numbers with percentages or units (e.g. 50%, 89%, 99%, 3 lần, 23%)
    has_stats = bool(re.search(r'\b\d+(?:\.\d+)?\s*(?:%|phần trăm|triệu|tỷ|tỉ|tỉ lệ|tỷ lệ|lượt|người)\b', text)) or bool(re.search(r'\d+%', text))
    
    # Look for explicit years (e.g. 2022, 2023, 2025)
    has_year = bool(re.search(r'\b(19|20)\d{2}\b', text))
    
    # Look for explicit source/citation keywords
    has_source_keywords = any(kw in text for kw in [
        "theo", "báo cáo", "nghiên cứu", "thống kê", "khảo sát", "hiệp hội", "tổ chức", "viện nghiên cứu", "đại học", "university", "report", "study"
    ])
    
    return (has_stats or has_year or has_source_keywords)

def search_duckduckgo(query: str, max_results: int = 3, client: httpx.Client = None) -> list[dict]:
    """Perform a DuckDuckGo HTML search and parse the links/snippets."""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    html = ""
    
    def fetch(c: httpx.Client) -> str:
        # Try up to 2 attempts with GET first, then fallback to POST
        for attempt in range(2):
            try:
                response = c.get(f"{url}?q={query}", timeout=12)
                if response.status_code == 200:
                    return response.text
                
                # Fallback to POST
                response = c.post(url, data={"q": query}, timeout=12)
                if response.status_code == 200:
                    return response.text
            except Exception:
                if attempt == 1:
                    return ""
        return ""

    if client is not None:
        html = fetch(client)
    else:
        with httpx.Client(headers=headers, follow_redirects=True) as local_client:
            html = fetch(local_client)
                
    if not html:
        return []
        
    try:
        # Extract link results using flexible regex that ignores attribute order
        links = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
        snippets = re.findall(r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
        if not snippets:
            snippets = re.findall(r'<div[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            
        results = []
        for i, (href, title) in enumerate(links[:max_results]):
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            
            url_clean = href
            if "/l/?uddg=" in href:
                match = re.search(r'uddg=([^&]+)', href)
                if match:
                    url_clean = urllib.parse.unquote(match.group(1))
            elif href.startswith("//"):
                url_clean = "https:" + href
                
            snippet_clean = ""
            if i < len(snippets):
                snippet_clean = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                
            results.append({
                "title": title_clean,
                "url": url_clean,
                "snippet": snippet_clean
            })
        return results
    except Exception:
        return []

def search_mojeek(query: str, max_results: int = 3, client: httpx.Client = None) -> list[dict]:
    """Perform a Mojeek search and parse the links/snippets as a fallback."""
    url = f"https://www.mojeek.com/search?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    html = ""
    try:
        if client is not None:
            response = client.get(url, timeout=12)
            if response.status_code == 200:
                html = response.text
        else:
            with httpx.Client(headers=headers, follow_redirects=True) as local_client:
                response = local_client.get(url, timeout=12)
                if response.status_code == 200:
                    html = response.text
    except Exception:
        return []
        
    if not html:
        return []
        
    try:
        import html as html_lib
        items = re.findall(r'<li class="r\d+">(.*?)</li>', html, re.DOTALL)
        results = []
        for item in items[:max_results]:
            title_match = re.search(r'<h2><a class="title"[^>]*>(.*?)</a></h2>', item, re.DOTALL)
            title_clean = ""
            if title_match:
                title_clean = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            
            url_match = re.search(r'<h2><a class="title"[^>]*href="([^"]+)"', item)
            url_clean = ""
            if url_match:
                url_clean = url_match.group(1).strip()
                
            snippet_match = re.search(r'<p class="s">(.*?)</p>', item, re.DOTALL)
            snippet_clean = ""
            if snippet_match:
                snippet_clean = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                
            if url_clean and title_clean:
                title_clean = html_lib.unescape(title_clean)
                snippet_clean = html_lib.unescape(snippet_clean)
                results.append({
                    "title": title_clean,
                    "url": url_clean,
                    "snippet": snippet_clean
                })
        return results
    except Exception:
        return []

def search_brave(query: str, max_results: int = 3, client: httpx.Client = None) -> list[dict]:
    """Perform a Brave search and parse the links/snippets as a fallback."""
    url = f"https://search.brave.com/search?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    html = ""
    try:
        if client is not None:
            response = client.get(url, timeout=12)
            if response.status_code == 200:
                html = response.text
        else:
            with httpx.Client(headers=headers, follow_redirects=True) as local_client:
                response = local_client.get(url, timeout=12)
                if response.status_code == 200:
                    html = response.text
    except Exception:
        return []
        
    if not html:
        return []
        
    try:
        import html as html_lib
        chunks = re.split(r'<div class="snippet\s+svelte-[^"]*"\s+data-pos="\d+"', html)
        blocks = chunks[1:]
        
        results = []
        for block in blocks[:max_results]:
            # Extract URL
            url_match = re.search(r'href="([^"]+)"[^>]*class="[^"]*l1[^"]*"', block)
            if not url_match:
                url_match = re.search(r'href="([^"]+)"', block)
            url_clean = url_match.group(1).strip() if url_match else ""
            
            # Extract Title
            title_match = re.search(r'class="title search-snippet-title[^"]*"\s+title="([^"]+)"', block)
            if not title_match:
                title_match = re.search(r'class="title search-snippet-title[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
            title_clean = ""
            if title_match:
                title_clean = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                title_clean = html_lib.unescape(title_clean)
                
            # Extract Snippet
            snippet_match = re.search(r'class="content desktop-default-regular[^"]*">(.*?)</div>', block, re.DOTALL)
            if not snippet_match:
                snippet_match = re.search(r'class="content[^"]*">(.*?)</div>', block, re.DOTALL)
            snippet_clean = ""
            if snippet_match:
                snippet_clean = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                snippet_clean = re.sub(r'<!--\[.*?\]-->', '', snippet_clean)
                snippet_clean = re.sub(r'<!---->', '', snippet_clean)
                snippet_clean = html_lib.unescape(snippet_clean).strip()
                
            if url_clean and title_clean:
                results.append({
                    "title": title_clean,
                    "url": url_clean,
                    "snippet": snippet_clean
                })
        return results
    except Exception:
        return []

def generate_search_query(user_argument: str, topic: str) -> str:
    """Use a quick LLM call to extract/formulate an English search query for fact-checking."""
    prompt = (
        "Bạn là trợ lý tìm kiếm. Hãy đọc lập luận của người dùng và tạo ra đúng một truy vấn tìm kiếm ngắn gọn (tối đa 6 từ) "
        "bằng tiếng Anh để tìm các nguồn tin cậy hỗ trợ hoặc bác bỏ số liệu/nguồn trích dẫn được nhắc đến. "
        "Luôn tạo truy vấn bằng tiếng Anh để tối ưu hóa kết quả tìm kiếm trên các công cụ tìm kiếm. "
        "Chỉ trả về duy nhất truy vấn tìm kiếm, không giải thích, không nháy kép.\n\n"
        f"Chủ đề tranh luận: {topic}\n"
        f"Lập luận người dùng: {user_argument}"
    )
    messages = [
        {"role": "system", "content": "Bạn chỉ trả về kết quả tìm kiếm duy nhất dưới dạng chuỗi văn bản trơn (plain text) bằng tiếng Anh."},
        {"role": "user", "content": prompt}
    ]
    res = call_groq(messages, max_tokens=30, temperature=0.0)
    if res["ok"]:
        query = res["text"].strip().strip('"').strip("'")
        return query
    return user_argument[:50]

def generate_rebuttal_search_query(topic: str, ai_stance: str) -> str:
    """Use a quick LLM call to extract/formulate an English search query for the AI's rebuttal evidence."""
    prompt = (
        "Bạn là trợ lý tìm kiếm. Hãy tạo đúng một truy vấn tìm kiếm ngắn gọn (tối đa 6 từ) "
        "bằng tiếng Anh để tìm các bài viết, nghiên cứu, hoặc số liệu cụ thể "
        f"nhằm ủng hộ lập trường '{ai_stance}' đối với chủ đề: '{topic}'. "
        "Luôn tạo truy vấn bằng tiếng Anh để tối ưu hóa kết quả tìm kiếm. "
        "Chỉ trả về duy nhất truy vấn tìm kiếm, không giải thích, không nháy kép."
    )
    messages = [
        {"role": "system", "content": "Bạn chỉ trả về kết quả tìm kiếm duy nhất dưới dạng chuỗi văn bản trơn (plain text) bằng tiếng Anh."},
        {"role": "user", "content": prompt}
    ]
    res = call_groq(messages, max_tokens=30, temperature=0.0)
    if res["ok"]:
        query = res["text"].strip().strip('"').strip("'")
        return query
    return f"{topic} {ai_stance} evidence"

def _fetch_user_fact_check_results(user_argument: str, topic: str, client: httpx.Client = None) -> list[dict]:
    if not should_search_for_factcheck(user_argument):
        return []
    query = generate_search_query(user_argument, topic)
    results = search_duckduckgo(query, max_results=3, client=client)
    if not results:
        results = search_brave(query, max_results=3, client=client)
    if not results:
        results = search_mojeek(query, max_results=3, client=client)
    if not results:
        words = [w for w in re.findall(r'\w+', user_argument) if w[0].isupper()]
        fallback_query = " ".join(words[:4])
        if fallback_query:
            results = search_duckduckgo(fallback_query, max_results=3, client=client)
            if not results:
                results = search_brave(fallback_query, max_results=3, client=client)
            if not results:
                results = search_mojeek(fallback_query, max_results=3, client=client)
    return results

def _fetch_ai_rebuttal_results(topic: str, ai_stance: str, client: httpx.Client = None) -> list[dict]:
    query = generate_rebuttal_search_query(topic, ai_stance)
    results = search_duckduckgo(query, max_results=3, client=client)
    if not results:
        results = search_brave(query, max_results=3, client=client)
    if not results:
        results = search_mojeek(query, max_results=3, client=client)
    if not results:
        fallback_query = f"{topic} {ai_stance} statistics"
        results = search_duckduckgo(fallback_query, max_results=3, client=client)
        if not results:
            results = search_brave(fallback_query, max_results=3, client=client)
        if not results:
            results = search_mojeek(fallback_query, max_results=3, client=client)
    return results

def get_combined_search_context(user_argument: str, topic: str, user_stance: str) -> tuple[str, str]:
    """
    Retrieve formatted search contexts for both user fact-checking and AI rebuttal evidence sequentially
    using a shared connection session and a random delay to prevent IP blocking.
    Returns:
        tuple[str, str]: (fact_check_context, ai_evidence_context)
    """
    ai_stance = "oppose" if user_stance == "support" else "support"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    user_results = []
    ai_results = []
    
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        # 1. Fetch user fact check results
        user_results = _fetch_user_fact_check_results(user_argument, topic, client=client)
        
        # 2. Random delay if user search returned results and we need to fetch AI results next
        if user_results:
            sleep_time = random.uniform(1.0, 2.0)
            time.sleep(sleep_time)
            
        # 3. Fetch AI rebuttal results
        ai_results = _fetch_ai_rebuttal_results(topic, ai_stance, client=client)
        
    # Format user fact check context
    user_context = ""
    if user_results:
        lines = ["=== KẾT QUẢ TÌM KIẾM INTERNET ĐỂ KIỂM CHỨNG BẰNG CHỨNG NGƯỜI DÙNG ==="]
        for idx, r in enumerate(user_results, 1):
            lines.append(f"Kết quả {idx}:")
            lines.append(f"  Tiêu đề: {r['title']}")
            lines.append(f"  URL: {r['url']}")
            lines.append(f"  Nội dung tóm tắt: {r['snippet']}")
        lines.append("=== KẾT THÚC KẾT QUẢ TÌM KIẾM KIỂM CHỨNG ===")
        user_context = "\n".join(lines)
        
    # Format AI rebuttal evidence context
    ai_context = ""
    if ai_results:
        lines = ["=== KẾT QUẢ TÌM KIẾM INTERNET ĐỂ AI LẤY BẰNG CHỨNG PHẢN BIỆN ==="]
        for idx, r in enumerate(ai_results, 1):
            lines.append(f"Kết quả {idx}:")
            lines.append(f"  Tiêu đề: {r['title']}")
            lines.append(f"  URL: {r['url']}")
            lines.append(f"  Nội dung tóm tắt: {r['snippet']}")
        lines.append("=== KẾT THÚC KẾT QUẢ TÌM KIẾM BẰNG CHỨNG AI ===")
        ai_context = "\n".join(lines)
        
    return user_context, ai_context

