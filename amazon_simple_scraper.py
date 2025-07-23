import requests
from bs4 import BeautifulSoup
import time
import csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_product_links(soup):
    products = []
    for div in soup.select('div.s-result-item[data-asin]'):
        asin = div.get('data-asin')
        a = div.select_one('a[href*="/dp/"]')
        if not a:
            continue
        href = a.get('href')
        url = href.split('?')[0]
        if not url.startswith('http'):
            url = 'https://www.amazon.com' + url
        products.append({
            'asin': asin,
            'url': url,
        })
    return products

def get_next_page_url(soup):
    next_btn = soup.select_one('a.s-pagination-next:not(.s-pagination-disabled)')
    if next_btn and next_btn.get('href'):
        return 'https://www.amazon.com' + next_btn['href']
    return None

def scrape_category(start_url, max_pages=400, delay=2):
    url = start_url
    all_products = []
    seen = set()
    for page in range(max_pages):
        print(f"Scraping page {page+1}: {url}")
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Failed to fetch page: {resp.status_code}")
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        products = get_product_links(soup)
        print(f"Found {len(products)} products.")
        for prod in products:
            key = (prod['asin'], prod['url'])
            if key not in seen:
                all_products.append(prod)
                seen.add(key)
        next_url = get_next_page_url(soup)
        if not next_url:
            print("No more pages.")
            break
        url = next_url
        time.sleep(delay)
    return all_products

def save_to_csv(products, filename="amazon_products_simple.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["asin", "url"])
        writer.writeheader()
        for prod in products:
            writer.writerow(prod)
    print(f"Saved {len(products)} products to {filename}")

if __name__ == "__main__":
    CATEGORY_URL = "https://www.amazon.com/s?i=fashion-womens-intl-ship&bbn=16225018011&rh=n%3A7141123011%2Cn%3A16225018011%2Cn%3A7147440011%2Cn%3A1040660%2Cn%3A1045024&dc&language=es&ds=v1%3A05d87YeSwnKfQs43WAEgAGbMi2y1eJ15PaCach5%2BoWo&qid=1753042248&rnid=1040660&ref=sr_nr_n_2"
    products = scrape_category(CATEGORY_URL, max_pages=400)
    save_to_csv(products) 