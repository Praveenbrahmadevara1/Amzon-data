from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app, origins=["*"])

@app.route("/scrape-product-urls", methods=["POST"])
def scrape_product_urls():
    data = request.get_json()
    category_urls = data.get("categoryUrls", [])
    limit = data.get("limit", 10)
    # Dummy: generate fake product URLs
    product_urls = []
    for i, cat_url in enumerate(category_urls):
        for j in range(min(limit, 5)):
            product_urls.append(f"{cat_url}/dp/FAKEASIN{i+1}{j+1}")
    # Simulate work
    time.sleep(1)
    return jsonify(productUrls=product_urls[:limit])

@app.route("/scrape-product-details", methods=["POST"])
def scrape_product_details():
    data = request.get_json()
    product_urls = data.get("productUrls", [])
    # Dummy: generate fake details
    details = []
    for url in product_urls:
        details.append({
            "url": url,
            "product_name": "Sample Product for " + url[-8:],
            "price": "$19.99",
            "currency": "$"
        })
    # Simulate work
    time.sleep(1)
    return jsonify(productDetails=details)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) 