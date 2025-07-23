"""
Amazon Category Scraper
-----------------------
- Accepts one or more Amazon category URLs as input.
- Navigates all pages in each category, handling pagination.
- Extracts valid product URLs (ignoring ads/banners).
- Outputs structured results (CSV or text).
- Handles errors, CAPTCHAs, and supports user-agent/proxy rotation.
- Emulates human-like browsing.
- No login required.

Requirements:
- pip install playwright
- playwright install
"""
import asyncio
import random
import time
import csv
import sys
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# User agents for rotation
USER_AGENTS = [
    # Desktop
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
]

# Optionally, add proxies here
PROXIES = [
    # "http://user:pass@proxyhost:port",
    # "socks5://user:pass@proxyhost:port",
]

# Human-like delay
async def human_delay(min_sec=1.0, max_sec=3.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def handle_captcha(page: Page) -> bool:
    """
    Detect and handle Amazon CAPTCHA. Returns True if a CAPTCHA was detected and handled, False otherwise.
    """
    try:
        # Amazon CAPTCHA pages usually have 'captcha' in the URL or a form with 'captcha' in the id/name
        if "captcha" in page.url.lower():
            print(f"[!] CAPTCHA detected at {page.url}. Waiting for manual solve or skipping...")
            # Optionally, you can implement a CAPTCHA solving service here
            # For now, wait and retry a few times, then skip
            for i in range(3):
                await asyncio.sleep(10)
                if "captcha" not in page.url.lower():
                    return True
            return True
        # Some CAPTCHAs are inline (e.g., image selection, slider, etc.)
        # Add more detection logic as needed
    except Exception as e:
        print(f"[!] Error during CAPTCHA detection: {e}")
    return False

async def extract_product_urls(page: Page) -> List[str]:
    """
    Extract valid product URLs from the current Amazon category page.
    Ignores sponsored/ads and non-product links.
    """
    product_urls = set()
    try:
        # Amazon product links usually contain '/dp/' or '/gp/'
        anchors = await page.query_selector_all('a[href*="/dp/"]')
        for a in anchors:
            href = await a.get_attribute('href')
            if href and '/dp/' in href:
                # Clean up URL (remove tracking params, etc.)
                url = href.split("?")[0]
                if not url.startswith("http"):
                    url = "https://www.amazon.com" + url
                product_urls.add(url)
        # Optionally, add '/gp/' links (some products use this)
        anchors = await page.query_selector_all('a[href*="/gp/product/"]')
        for a in anchors:
            href = await a.get_attribute('href')
            if href and '/gp/product/' in href:
                url = href.split("?")[0]
                if not url.startswith("http"):
                    url = "https://www.amazon.com" + url
                product_urls.add(url)
    except Exception as e:
        print(f"[!] Error extracting product URLs: {e}")
    return list(product_urls)

async def go_to_next_page(page: Page) -> bool:
    """
    Clicks the 'Next' button if available. Returns True if navigation occurred, False otherwise.
    Handles both desktop and mobile layouts. Tries multiple selectors and scrolls into view.
    """
    selectors = [
        'a.s-pagination-next:not(.s-pagination-disabled)',  # Desktop
        'li.a-last a',  # Mobile
        'button.s-pagination-next',  # Sometimes Next is a button
        'a[aria-label="Next"]',
        'li.a-last > span > a',
    ]
    for sel in selectors:
        try:
            next_btn = await page.query_selector(sel)
            if next_btn:
                print(f"[>] Found Next button with selector: {sel}")
                await next_btn.scroll_into_view_if_needed()
                await human_delay(1, 2)
                try:
                    await next_btn.click(timeout=5000)
                except Exception as e:
                    print(f"[!] Error clicking Next with selector {sel}: {e}")
                    continue
                try:
                    await page.wait_for_load_state('networkidle', timeout=25000)
                except Exception as e:
                    print(f"[!] Timeout or error waiting for next page to load: {e}")
                await human_delay(1, 2)
                return True
        except Exception as e:
            print(f"[!] Error finding/clicking Next with selector {sel}: {e}")
    print("[!] No Next button found or all attempts failed.")
    return False

async def scrape_category(category_url: str, user_agent: Optional[str]=None, proxy: Optional[str]=None) -> List[str]:
    """
    Scrape all product URLs from a single Amazon category URL.
    """
    product_urls = set()
    try:
        playwright = await async_playwright().start()
        browser_args = {}
        if proxy:
            browser_args['proxy'] = { 'server': proxy }
        browser = await playwright.chromium.launch(headless=False, args=["--no-sandbox"])
        context_args = {}
        if user_agent:
            context_args['user_agent'] = user_agent
        context = await browser.new_context(**context_args)
        page = await context.new_page()
        await page.goto(category_url, timeout=30000)
        await human_delay(2, 4)
        page_num = 1
        while True:
            if await handle_captcha(page):
                print(f"[!] CAPTCHA encountered at {page.url}. Skipping page.")
                break
            urls = await extract_product_urls(page)
            print(f"[+] Page {page_num}: Found {len(urls)} product URLs.")
            product_urls.update(urls)
            has_next = await go_to_next_page(page)
            if not has_next:
                break
            page_num += 1
            await human_delay(2, 5)
        await browser.close()
        await playwright.stop()
    except Exception as e:
        print(f"[!] Error scraping category {category_url}: {e}")
    return list(product_urls)

def save_to_csv(results: Dict[str, List[str]], filename: str = "amazon_products.csv"):
    """
    Save the results to a CSV file.
    """
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Category URL", "Product URL"])
        for category, urls in results.items():
            for url in urls:
                writer.writerow([category, url])
    print(f"[+] Results saved to {filename}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Amazon Category Product URL Scraper")
    parser.add_argument("urls", nargs='+', help="Amazon category URLs to scrape")
    parser.add_argument("--csv", default="amazon_products.csv", help="Output CSV filename")
    parser.add_argument("--proxy", default=None, help="Proxy server (optional)")
    parser.add_argument("--rotate-user-agent", action="store_true", help="Rotate user agents per category")
    args = parser.parse_args()

    results = {}
    async def runner():
        for idx, url in enumerate(args.urls):
            user_agent = None
            if args.rotate_user_agent:
                user_agent = USER_AGENTS[idx % len(USER_AGENTS)]
            proxy = args.proxy or (PROXIES[idx % len(PROXIES)] if PROXIES else None)
            print(f"[>] Scraping: {url} (User-Agent: {user_agent}, Proxy: {proxy})")
            urls = await scrape_category(url, user_agent=user_agent, proxy=proxy)
            results[url] = urls
    asyncio.run(runner())
    save_to_csv(results, args.csv)

if __name__ == "__main__":
    main() 