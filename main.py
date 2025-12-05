# main.py
from playwright_scraper import scrape_listing
from market_estimator import estimate_market_price
from send_telegram import send_message

# Configuración mínima
MIN_PROFIT_PERCENT = 0.20
MIN_PROFIT_EUROS = 15

# Lista de URLs de outlet / ventas privadas que quieres monitorizar
LISTINGS = [
    "https://www.zalando-prive.es/sale",
    "https://www.privalia.com/es/sale",
    "https://www.showroomprive.com/sale"
]

def main():
    for url in LISTINGS:
        products = scrape_listing(url, max_products=30)
        for p in products:
            market_price = estimate_market_price(p["title"])
            if not market_price or not p["price_outlet"]:
                continue
            profit = market_price - p["price_outlet"]
            profit_percent = profit / p["price_outlet"]
            if profit >= MIN_PROFIT_EUROS and profit_percent >= MIN_PROFIT_PERCENT:
                sizes = ", ".join(p["sizes"]) if p["sizes"] else "todas"
                text = f"<b>{p['title']}</b>\nPrecio outlet: {p['price_outlet']}€\nPrecio estimado mercado: {market_price}€\nTamaños: {sizes}\nURL: {p['url']}"
                send_message(text)

if __name__ == "__main__":
    main()
