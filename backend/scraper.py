import requests
from bs4 import BeautifulSoup
import time

MAX_BATCH_SIZE = 5  # Limit number of products per call

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_category_urls(category_urls, limit=100):
    all_product_urls = []
    for cat_url in category_urls:
        product_urls = []
        page = 1
        while len(product_urls) < limit:
            url = f"{cat_url}&page={page}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(resp.text, "html.parser")
                found = 0
                for div in soup.select('div.s-result-item[data-asin]'):
                    a = div.select_one('a[href*="/dp/"]')
                    if not a:
                        continue
                    href = a.get('href').split('?')[0]
                    if not href.startswith('http'):
                        href = 'https://www.amazon.com' + href
                    product_urls.append(href)
                    found += 1
                    if len(product_urls) >= limit:
                        break
                if found == 0:
                    break
                page += 1
                time.sleep(1)
            except Exception:
                break
        all_product_urls.extend(product_urls[:limit])
    return all_product_urls[:limit]

def scrape_product_details(product_urls):
    results = []
    MAX_SIZE = 200_000  # 200 KB
    if len(product_urls) > MAX_BATCH_SIZE:
        return [{
            "url": None,
            "product_name": "ERROR: Too many URLs in one request (max %d)" % MAX_BATCH_SIZE,
            "price": "N/A",
            "currency": "N/A"
        }]
    for url in product_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            html = resp.text
            if len(html) > MAX_SIZE:
                print(f"Response too large for {url}")
                results.append({
                    "url": url,
                    "product_name": "TOO_LARGE",
                    "price": "N/A",
                    "currency": "N/A"
                })
                continue
            if ("Enter the characters you see below" in html or
                "Type the characters you see in this image" in html or
                "To discuss automated access to Amazon data" in html):
                print(f"CAPTCHA/interstitial detected for {url}")
                results.append({
                    "url": url,
                    "product_name": "BLOCKED",
                    "price": "N/A",
                    "currency": "N/A"
                })
                continue
            soup = BeautifulSoup(html, "html.parser")
            # Title extraction
            title = None
            for sel in ['#productTitle', '.product-title-word-break', 'h1.a-size-large', 'h1', 'meta[name=\"title\"]', 'meta[property=\"og:title\"]']:
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    title = el.get_text(strip=True)
                    break
                if el and el.has_attr('content'):
                    title = el['content']
                    break
            if not title:
                title = "N/A"
            # Price extraction
            price = None
            for sel in ['#priceblock_ourprice', '#priceblock_dealprice', '#priceblock_saleprice', '.a-price .a-offscreen']:
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    price = el.get_text(strip=True)
                    break
            if not price:
                price = "N/A"
            # Currency extraction
            currency = price[0] if price and price[0] in "$₹£€" else "N/A"
            results.append({
                "url": url,
                "product_name": title,
                "price": price,
                "currency": currency
            })
        except requests.Timeout:
            print(f"Timeout scraping {url}")
            results.append({
                "url": url,
                "product_name": "TIMEOUT",
                "price": "N/A",
                "currency": "N/A"
            })
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            results.append({
                "url": url,
                "product_name": "ERROR",
                "price": "N/A",
                "currency": "N/A"
            })
    return results 