# playwright_scraper.py
from playwright.sync_api import sync_playwright
import re
import json
from urllib.parse import urljoin

def extract_from_jsonld(page):
    try:
        jsonlds = page.query_selector_all("script[type='application/ld+json']")
        for s in jsonlds:
            txt = s.inner_text().strip()
            if not txt:
                continue
            try:
                data = json.loads(txt)
            except:
                try:
                    txt2 = txt.strip()
                    if txt2[0] == "[":
                        data = json.loads(txt2)
                    else:
                        continue
                except:
                    continue
            if isinstance(data, list):
                for el in data:
                    if isinstance(el, dict) and el.get("offers"):
                        return el
            if isinstance(data, dict) and data.get("offers"):
                return data
    except Exception:
        pass
    return None

def parse_price_text(txt):
    if not txt:
        return None
    txt = txt.replace("\xa0", " ")
    m = re.search(r"(\d{1,3}(?:[.,]\d{3})*[.,]\d{2}|\d+[.,]\d+|\d+)\s*€", txt)
    if m:
        val = m.group(1)
        val = val.replace('.', '').replace(',', '.')
        try:
            return float(val)
        except:
            return None
    return None

def extract_product_info_from_page(page, url):
    title = None
    try:
        og = page.query_selector('meta[property="og:title"]')
        if og:
            title = og.get_attribute("content")
    except:
        pass
    if not title:
        try:
            h1 = page.query_selector("h1")
            if h1:
                title = h1.inner_text().strip()
        except:
            pass

    jsonld = extract_from_jsonld(page)
    price = None
    currency = None
    if jsonld:
        offers = jsonld.get("offers")
        if isinstance(offers, list):
            offer = offers[0]
        else:
            offer = offers
        if isinstance(offer, dict):
            price_raw = offer.get("price") or offer.get("priceSpecification", {}).get("price")
            price = float(price_raw) if price_raw not in (None, "") else None
            currency = offer.get("priceCurrency") or offer.get("currency")
    if price is None:
        try:
            text = page.content()
            price = parse_price_text(text)
        except:
            price = None

    sizes = []
    try:
        size_elements = page.query_selector_all('button, span, li')
        for el in size_elements:
            txt = el.inner_text().strip()
            if re.match(r'^\d{1,2}(\.\d)?$', txt) or re.match(r'^[\d]{1,2}\s?EU$', txt, re.I):
                sizes.append(txt)
    except:
        sizes = []

    return {
        "url": url,
        "title": title or "",
        "price_outlet": price,
        "currency": currency or "EUR",
        "sizes": list(dict.fromkeys(sizes))
    }

def collect_product_links_from_listing(page, base_url, max_links=60):
    anchors = page.query_selector_all("a[href]")
    links = []
    for a in anchors:
        href = a.get_attribute("href")
        if not href:
            continue
        if href.startswith("http"):
            full = href
        else:
            full = urljoin(base_url, href)
        if any(x in full.lower() for x in ["/account", "/cart", "/login", "/checkout", "mailto:"]):
            continue
        if re.search(r'/(product|producto|p/|item|detail|offer|sale)/', full, re.I) or re.search(r'/[a-z0-9\-]+-\d{2,6}$', full):
            links.append(full)
        else:
            if len(full) > 40 and ('/brand' not in full):
                links.append(full)
    seen = []
    out = []
    for u in links:
        if u not in seen:
            seen.append(u)
            out.append(u)
        if len(out) >= max_links:
            break
    return out

def scrape_listing(url, max_products=40, wait_for_load=2000):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Timeout aumentado a 60000 ms
        page.goto(url, timeout=60000)
        page.wait_for_timeout(wait_for_load)
        product_links = collect_product_links_from_listing(page, url, max_links=max_products)
        for link in product_links:
            try:
                page.goto(link, timeout=60000)  # Timeout aumentado
                page.wait_for_timeout(1200)
                info = extract_product_info_from_page(page, link)
                results.append(info)
            except Exception as e:
                print("Error visitando", link, e)
                continue
        browser.close()
    return results
