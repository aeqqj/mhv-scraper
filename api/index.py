from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

app = FastAPI()

SITES = [
    "https://mountainhomesvail.com/arrabelleatvailsquare",
    "https://mountainhomesvail.com/theapogeon",
    "https://mountainhomesvail.com/solaris",
    "https://mountainhomesvail.com/primaresidences",
    "https://mountainhomesvail.com/thelodgeaptcondo",
    "https://mountainhomesvail.com/goldenpeakcondominiums",
    "https://mountainhomesvail.com/vailmountainviewresidences",
    "https://mountainhomesvail.com/altus",
]

def dismiss_popup(page):
    try:
        page.evaluate("""
            document.querySelector('.pop.sign-log').style.visibility = 'hidden'
            document.querySelector('.pop-mask').style.display = 'none'
            document.querySelector('.pop.sign-log').style.display = 'none'
        """)
    except:
        pass

def scrape_listing(page, url):
    page.goto(url)
    page.wait_for_load_state("networkidle")
    dismiss_popup(page)

    try:
        page.wait_for_selector("div.play", timeout=5000)
        page.click("div.play")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("i.iconfont.icon-close-light", timeout=3000)
        page.click("i.iconfont.icon-close-light")
    except:
        pass

    mls_id = page.eval_on_selector_all(
        "div.property-item",
        """items => {
            const match = items.find(el => el.querySelector('.item-label')?.innerText === 'MLS Listing ID')
            return match ? match.querySelector('.item-value').innerText : null
        }"""
    )
    price = page.query_selector("span.price-number")
    address = page.query_selector("div.inline-address")
    beds = page.query_selector("div.item-basic.bed-count .item-value")
    baths = page.query_selector("div.item-basic.bath-count .item-value")

    return {
        "Listing ID": mls_id if mls_id else None,
        "Price": price.inner_text().strip() if price else None,
        "Address": address.inner_text().strip() if address else None,
        "Beds": beds.inner_text().strip() if beds else None,
        "Baths": baths.inner_text().strip() if baths else None,
        "Source URL": url,
    }

def scrape_site(page, site_url):
    page.goto(site_url)
    page.wait_for_load_state("networkidle")
    dismiss_popup(page)

    try:
        page.wait_for_selector("div.house-item", timeout=10000)
    except:
        return []

    listings = page.query_selector_all("div.house-item")
    urls = []
    for listing in listings:
        link = listing.query_selector("a.house-preview")
        if link:
            href = link.get_attribute("href")
            if href:
                urls.append("https://mountainhomesvail.com" + href)

    results = []
    for url in urls:
        try:
            result = scrape_listing(page, url)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "Source URL": url})

    return results

@app.get("/scrape")
def scrape():
    all_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        Stealth()

        for site_url in SITES:
            site_name = site_url.split("/")[-1]
            try:
                listings = scrape_site(page, site_url)
                all_results[site_name] = listings
            except:
                all_results[site_name] = []

        browser.close()

    return all_results
