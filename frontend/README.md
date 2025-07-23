# Amazon Scraper Frontend

A modern, responsive React + TypeScript UI for scraping Amazon product URLs and details via your backend API.

## Features
- Input category URLs manually or via CSV/XLSX upload
- Limit number of product URLs to extract
- Scrape product URLs and product details in two steps
- Real-time progress, cancel scraping, and log console
- Download results as Excel (.xlsx)
- Mobile-friendly, accessible, and robust error handling

## Local Development

1. Clone this repo and `cd amazon-scraper-frontend`
2. Copy `.env.example` to `.env` and set your backend URL:
   ```
   REACT_APP_BACKEND_URL=http://localhost:5000
   ```
3. Install dependencies:
   ```
   npm install
   ```
4. Start the frontend:
   ```
   npm start
   ```

## Build & Deploy (Static Site)

1. Build for production:
   ```
   npm run build
   ```
2. Deploy the `build/` folder to Render, Netlify, Vercel, or any static host.

## Backend API Requirements
- `POST /scrape-product-urls` `{ categoryUrls: [...], limit }` → `[productUrl, ...]`
- `POST /scrape-product-details` `{ productUrls: [...] }` → `[{ url, product_name, price, currency }, ...]`
- (Optional) `/cancel-scrape` endpoint for job cancellation
- CORS must be enabled for frontend domain

## CORS/Proxy Tips
- If deploying backend and frontend separately, ensure CORS headers are set on backend.
- For local dev, you can use a proxy in `package.json` or set CORS on backend.

## Accessibility & Mobile
- All controls are keyboard accessible and ARIA-labeled.
- Layout is responsive for desktop and mobile.

## Log Console Upgrade
- The log console is ready for SSE/WebSocket if your backend supports real-time logs.
- See `src/App.tsx` for where to integrate SSE/WebSocket.

## Support
Open an issue or PR for improvements!
