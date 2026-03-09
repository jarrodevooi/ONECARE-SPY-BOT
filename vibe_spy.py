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
    context = browser.new_context(viewport={"width": 1280, "height": 3000})
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    
    # --- AGGRESSIVE SCROLL & CLICK LOOP ---
    last_height = page.evaluate("document.body.scrollHeight")
    for i in range(10):  # Try 10 times to find more ads
        # 1. Scroll to the bottom using the 'End' key
        page.keyboard.press("End")
        time.sleep(3)
        
        # 2. Try to click "See More" or "Lihat Lagi" if it appears
        try:
            # Using a broader selector to find the button
            see_more = page.locator('div[role="button"]:has-text("See More"), div[role="button"]:has-text("Lihat Lagi"), button:has-text("See More")')
            if see_more.is_visible():
                see_more.click(force=True)
                print(f"Loop {i+1}: Clicked See More")
                time.sleep(4)
        except:
            pass
            
        # 3. Check if the page actually grew
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height and i > 3: # If no growth after 4 tries, we're likely done
            break
        last_height = new_height
    # ---------------------------------------

    ad_ids = page.get_by_text(re.compile(r"ID Pustaka:|ID:", re.IGNORECASE)).all()
    count = len(ad_ids)
    
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
