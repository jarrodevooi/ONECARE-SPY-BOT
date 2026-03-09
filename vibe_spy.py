import os, re, time, requests
from playwright.sync_api import Playwright, sync_playwright

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&view_all_page_id=141890315998188&sort_data[mode]=total_impressions&sort_data[direction]=desc"

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 1200})
    page = context.new_page()
    
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(10) 

    # --- THE SHIELD BREAKER ---
    # Click 'Accept Cookies' or 'Close' on any country pop-ups that block the scroll
    try:
        # Closes the common 'Select Country' or 'Cookie' overlays
        page.get_by_role("button", name=re.compile(r"Accept|Allow|Allow all|Tutup|Close", re.IGNORECASE)).first.click(timeout=5000)
        print("Shield Breaker: Cleared overlays.")
        time.sleep(2)
    except:
        pass

    all_captured_ids = set()

    # --- THE SCANNING SCROLL ---
    for i in range(15):
        current_html = page.content()
        # Captures IDs even if Meta tries to hide them in the DOM
        found_now = re.findall(r"ID(?:\sPustaka)?:\s?(\d{15,16})", current_html)
        
        for ad_id in found_now:
            all_captured_ids.add(ad_id)
        
        print(f"Scroll {i+1}: Total in memory: {len(all_captured_ids)}")

        # Smooth human-like scroll
        page.mouse.wheel(0, 1500)
        time.sleep(4)

        # Handle 'See More' block
        try:
            btn = page.get_by_role("button", name=re.compile(r"See More|Lihat Lagi|More", re.IGNORECASE)).first
            if btn.is_visible():
                btn.click(force=True)
                time.sleep(4)
        except:
            pass

    count = len(all_captured_ids)
    
    # Fallback to counting "Active" labels if ID scraping fails
    if count == 0:
        active_labels = re.findall(r"Active|Aktif", page.content(), re.IGNORECASE)
        count = len(active_labels)

    image_path = "snapshot.png"
    # Take a screenshot of the top of the feed to confirm it's not a blank page
    page.screenshot(path=image_path)
    browser.close()
    return count, image_path

if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            current_count, img_path = get_ad_data(playwright)
            send_telegram_photo(f"✅ Onecare Spy Report: {current_count} ads found.", img_path)
            print(f"Done! Final Count: {current_count}")
        except Exception as e:
            print(f"Error: {e}")
