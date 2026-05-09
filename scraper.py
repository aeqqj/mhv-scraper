from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

app = FastAPI()

def dismiss_popup(page):
    try:
        page.evaluate("""
            document.querySelector('.pop.sign-log').style.visibility = 'hidden'
            document.querySelector('.pop-mask').style.display = 'none'
            document.querySelector('.pop.sign-log').style.display = 'none'
        """)
    except:
        pass

@app.get("/scrape")
def scrape():
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

        page.goto("https://mountainhomesvail.com/arrabelleatvailsquare")
        page.wait_for_load_state("networkidle")
        dismiss_popup(page)
        page.wait_for_selector("div.house-item", timeout=10000)

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
            page.goto(url)
            page.wait_for_load_state("networkidle")
            dismiss_popup(page)

            try:
                page.wait_for_selector("div.play", timeout=3000)
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

            results.append({
                "Listing ID": mls_id if mls_id else None,
                "Price": price.inner_text().strip() if price else None,
                "Address": address.inner_text().strip() if address else None,
                "Beds": beds.inner_text().strip() if beds else None,
                "Baths": baths.inner_text().strip() if baths else None,
            })

        browser.close()
        return {"listings": results}
