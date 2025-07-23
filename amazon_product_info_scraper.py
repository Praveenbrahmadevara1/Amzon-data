import requests
from bs4 import BeautifulSoup
import time
import random
import csv
import json
import logging
import re
from urllib.parse import urlparse

class AmazonProductInfoScraper:
    def __init__(self, user_agents=None, delay_range=(1, 3), timeout=15, log_file='scraper.log'):
        self.session = requests.Session()
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        ]
        self.delay_range = delay_range
        self.timeout = timeout
        self.failed_html_saved = False
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

    def fetch_product_info(self, product_url):
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
        }
        try:
            resp = self.session.get(product_url, headers=headers, timeout=self.timeout)
            print(f"[DEBUG] Fetched {resp.url} (status {resp.status_code})")
            if resp.status_code != 200:
                logging.error(f"Failed to fetch {product_url}: Status {resp.status_code}")
                return self._empty_result(product_url, reason=f"HTTP {resp.status_code}")
            soup = BeautifulSoup(resp.text, "html.parser")
            if self.is_captcha_page(soup, resp.text):
                logging.error(f"CAPTCHA detected for {product_url}")
                print(f"[ERROR] CAPTCHA detected for {product_url}")
                if not self.failed_html_saved:
                    with open('debug_failed_product.html', 'w', encoding='utf-8') as f:
                        f.write(resp.text)
                    self.failed_html_saved = True
                return self._empty_result(product_url, reason="CAPTCHA detected")
            if self.is_interstitial(resp.text):
                logging.warning(f"Blocked/interstitial page for URL: {product_url}")
                return self._empty_result(product_url, reason="Blocked/interstitial page")
            title = self.extract_title(soup)
            price, currency = self.extract_price_and_currency(soup, product_url)
            if not title:
                print(f"[WARN] No title found for {product_url}")
                logging.warning(f"No title found for {product_url}")
            if not price:
                print(f"[WARN] No price found for {product_url}")
                logging.warning(f"No price found for {product_url}")
            if (not title or not price) and not self.failed_html_saved:
                with open('debug_failed_product.html', 'w', encoding='utf-8') as f:
                    f.write(resp.text)
                print(f"[DEBUG] Saved failed HTML for {product_url}")
                self.failed_html_saved = True
                print(f"[DEBUG] First 500 chars of HTML: {resp.text[:500]}")
            if not title:
                title = "N/A"
            if not price:
                price = "N/A"
            if not currency:
                currency = self.infer_currency_from_url(product_url)
            return {
                "url": product_url,
                "product_name": title.strip() if title else "N/A",
                "price": price,
                "currency": currency,
            }
        except Exception as e:
            logging.error(f"Exception for {product_url}: {e}")
            print(f"[ERROR] Exception for {product_url}: {e}")
            return self._empty_result(product_url, reason=str(e))
        finally:
            time.sleep(random.uniform(*self.delay_range))

    def is_captcha_page(self, soup, html):
        # Amazon CAPTCHA pages often have 'captcha' in the title or a form with 'captcha' in the action
        if soup.title and 'captcha' in soup.title.text.lower():
            return True
        if soup.find('form', {'action': re.compile('captcha', re.I)}):
            return True
        if 'Type the characters you see in this image' in html:
            return True
        if 'Enter the characters you see below' in html:
            return True
        return False

    def is_interstitial(self, html):
        """Detect Amazon bot-detection/interstitial pages."""
        triggers = [
            "Continue shopping",
            "Conditions of Use",
            "To discuss automated access to Amazon data",
            "Sorry, we just need to make sure you're not a robot.",
            "Enter the characters you see below",
            "Type the characters you see in this image",
        ]
        return any(trigger in html for trigger in triggers)

    def extract_title(self, soup):
        selectors = [
            ('#productTitle', 'id'),
            ('.product-title-word-break', 'class'),
            ('h1.a-size-large', 'h1-class'),
            ('h1', 'h1-generic'),
            ('meta[name="title"]', 'meta-title'),
            ('meta[property="og:title"]', 'og-title'),
        ]
        for sel, label in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                logging.info(f"Title found using {label} selector.")
                return el.get_text(strip=True)
            if el and el.has_attr('content'):
                logging.info(f"Title found using {label} meta content.")
                return el['content']
        # Try <title> tag as last resort
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text(strip=True):
            logging.info("Title found using <title> tag fallback.")
            return title_tag.get_text(strip=True)
        # If still not found, save HTML for debugging
        with open('debug_title_not_found.html', 'w', encoding='utf-8') as f:
            f.write(str(soup))
        logging.warning("No title found, saved HTML to debug_title_not_found.html")
        return "N/A"

    def extract_price_and_currency(self, soup, url):
        price_selectors = [
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#priceblock_saleprice',
            '#priceblock_pospromoprice',
            '#priceblock_businessprice',
            '#priceblock_snsprice_Based',
            'span.a-price.a-text-price span.a-offscreen',
            'span.a-price span.a-offscreen',
            'span.a-price-whole',
        ]
        price = None
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el and el.text.strip():
                price = el.text.strip()
                break
        if not price:
            text = soup.get_text()
            match = re.search(r'([\$\£\€\₹])\s?([\d,]+\.\d{2})', text)
            if match:
                price = match.group(0)
        currency = None
        if price:
            match = re.match(r'([\$\£\€\₹])', price)
            if match:
                currency = match.group(1)
            else:
                currency = self.infer_currency_from_url(url)
        return price, currency

    def infer_currency_from_url(self, url):
        tld = urlparse(url).netloc.split('.')[-1]
        return {
            'com': '$',
            'in': '₹',
            'co': '£',
            'uk': '£',
            'de': '€',
            'fr': '€',
            'es': '€',
            'it': '€',
            'jp': '¥',
            'ca': '$',
            'mx': '$',
            'au': '$',
        }.get(tld, '')

    def _empty_result(self, url, reason=None):
        return {
            "url": url,
            "product_name": "N/A",
            "price": "N/A",
            "currency": "N/A",
            "error": reason or "Extraction failed"
        }

    def process_urls(self, url_list):
        results = []
        for url in url_list:
            info = self.fetch_product_info(url)
            results.append(info)
        return results

    def save_results(self, data, format='csv', filename='amazon_product_info_output'):
        if format == 'csv':
            fname = filename if filename.endswith('.csv') else filename + '.csv'
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["url", "product_name", "price", "currency"])
                writer.writeheader()
                for row in data:
                    writer.writerow({k: row.get(k, "N/A") for k in ["url", "product_name", "price", "currency"]})
        elif format == 'json':
            fname = filename if filename.endswith('.json') else filename + '.json'
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} records to {fname}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Amazon Product Info Scraper")
    parser.add_argument('input', help='Input file with product URLs (one per line)')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')
    parser.add_argument('--output', default='amazon_product_info_output', help='Output file name (no extension)')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    scraper = AmazonProductInfoScraper()
    results = scraper.process_urls(urls)
    scraper.save_results(results, format=args.format, filename=args.output)
    print(f"[SUMMARY] Processed {len(urls)} URLs. See output and logs for details.") 