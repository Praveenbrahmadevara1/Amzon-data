from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import scrape_category_urls, scrape_product_details
import os
import re

app = Flask(__name__)
CORS(app, origins=["*"])

@app.route("/scrape-product-urls", methods=["POST"])
def scrape_product_urls_endpoint():
    data = request.get_json()
    category_urls = data.get("categoryUrls", [])
    limit = data.get("limit", 10)
    product_urls = scrape_category_urls(category_urls, limit)
    return jsonify(productUrls=product_urls)

@app.route("/scrape-product-details", methods=["POST"])
def scrape_product_details_endpoint():
    data = request.get_json()
    product_urls = data.get("productUrls", [])
    details = scrape_product_details(product_urls)
    return jsonify(productDetails=details)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) 