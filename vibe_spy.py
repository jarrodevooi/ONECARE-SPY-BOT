import os, re, time, requests
from playwright.sync_api import Playwright, sync_playwright

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# Direct Page ID link for Onecare
TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&view_all_page_id=141890315998188&sort_data[mode]=total_impressions&sort_data[direction]=desc"

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 1200})
    page = context.new_page()
    
    # 1. Start with the direct Page ID link
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    time.sleep(8) 

    # This 'set' acts as your permanent memory bank
    all_captured_ids = set()

    # 2. The "Scanning Scroll"
    for i in range(15):
        # Scan the current viewable HTML for any Ad IDs
        current_html = page.content()
        # Regex for 15-16 digit Meta Ad IDs
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

    # 3. Final count from your memory, not from the current screen
    count = len(all_captured_ids)
    
    # If the count is still low, Meta might have changed the 'ID' label again
    if count == 0:
        # Emergency fallback: count anything that looks like an Ad ID number
        fallback_ids = re.findall(r"\"ad_id\":\"(\d+)\"|id\":(\d{15,16})", page.content())
        count = len(set(fallback_ids))

    image_path = "snapshot.png"
    page.screenshot(path=image_path, full_page=True)
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
