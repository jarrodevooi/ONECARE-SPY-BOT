import os, re, time, requests
from playwright.sync_api import Playwright, sync_playwright

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# Using the direct Page ID link for Onecare to ensure we get the full 68+ ads
TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&view_all_page_id=141890315998188&sort_data[mode]=total_impressions&sort_data[direction]=desc"

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 1000})
    page = context.new_page()

    captured_ids = set()

    # --- IMPROVED SNIFFER ---
    def handle_response(response):
        # Listen to ALL data coming from Facebook's servers
        if "graphql" in response.url or "ads/library" in response.url:
            try:
                # We extract the raw text and look for Ad ID patterns
                body = response.text()
                # Meta Ad IDs are usually 15-16 digit strings
                found = re.findall(r'"ad_id":"(\d+)"|id":(\d{15,16})', body)
                for pair in found:
                    for ad_id in pair:
                        if ad_id: captured_ids.add(ad_id)
            except:
                pass

    page.on("response", handle_response)
    
    # 1. Load the page and wait for the first batch
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(10) # Initial soak time

    # 2. Aggressive Scroll to force Meta to send more data packets
    for i in range(12):
        page.mouse.wheel(0, 2500) 
        time.sleep(4) 
        # Click "See More" if it blocks the flow
        try:
            btn = page.locator('div[role="button"]:has-text("More"), div[role="button"]:has-text("Lagi")').first
            if btn.is_visible():
                btn.click(force=True)
                time.sleep(4)
        except:
            pass
        print(f"Progress: Captured {len(captured_ids)} unique ads...")

    # 3. Final Count
    count = len(captured_ids)
    if count == 0:
        # Fallback: If sniffer fails, try a manual count of the visible IDs
        ids_on_page = re.findall(r"ID(?:\sPustaka)?:\s?(\d+)", page.content())
        count = len(set(ids_on_page))

    image_path = "snapshot.png"
    page.screenshot(path=image_path, full_page=True)
    browser.close()
    return count, image_path

if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            current_count, img_path = get_ad_data(playwright)
            send_telegram_photo(f"✅ Onecare Spy Report: {current_count} ads found.", img_path)
            print(f"Final Result: {current_count} ads sent to Telegram.")
        except Exception as e:
            print(f"Error: {e}")
