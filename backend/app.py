from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from scraper import scrape_category_urls, scrape_product_details
import os
import re

app = Flask(__name__)
CORS(app, origins=["*"])

FRONTEND_URL = "https://amzon-data-frontend.onrender.com"  # Update this if your frontend URL is different

@app.route("/", methods=["GET"])
def root():
    return redirect(FRONTEND_URL, code=302)

@app.route("/scrape-product-urls", methods=["POST"])
def scrape_product_urls_endpoint():
    data = request.get_json()
    # Default limit is now 200
    category_urls = data.get("categoryUrls", [])
    limit = data.get("limit", 200)
    product_urls = scrape_category_urls(category_urls, limit)
    return jsonify(productUrls=product_urls)

@app.route("/scrape-product-details", methods=["POST"])
def scrape_product_details_endpoint():
    try:
        data = request.get_json()
        product_urls = data.get("productUrls", [])
        details = scrape_product_details(product_urls)
        return jsonify(productDetails=details)
    except Exception as e:
        print(f"API error in /scrape-product-details: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) 