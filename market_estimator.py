# market_estimator.py
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent":"Mozilla/5.0"}

def extract_prices_from_vinted_html(html):
    soup = BeautifulSoup(html, "html.parser")
    prices = []
    for tag in soup.find_all(text=re.compile(r'\d+[,\.]?\d*\s*€')):
        txt = tag.strip()
        m = re.search(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2}|\d+[.,]\d+|\d+)\s*€', txt)
        if m:
            val = m.group(1).replace('.', '').replace(',', '.')
            try:
                prices.append(float(val))
            except:
                continue
    return prices

def estimate_price_vinted(query, limit=30):
    url = f"https://www.vinted.es/catalog?search_text={requests.utils.quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        prices = extract_prices_from_vinted_html(r.text)
        if not prices:
            return None
        prices_sorted = sorted(prices)
        mid = prices_sorted[len(prices_sorted)//2]
        return mid
    except Exception:
        return None

def estimate_market_price(title):
    v = estimate_price_vinted(title)
    if v:
        return v
    return None
