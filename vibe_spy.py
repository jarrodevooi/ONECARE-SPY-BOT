import os
import re
import time
import requests
from playwright.sync_api import Playwright, sync_playwright

# Pulls from the Secrets "Vault" you already set up
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&q=onecare&search_type=keyword_unordered&sort_data[mode]=total_impressions&sort_data[direction]=desc"

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    # Use a standard desktop view but we will scroll it like a pro
    context = browser.new_context(viewport={"width": 1280, "height": 900}) 
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    time.sleep(7)

    all_found_ids = set() # This is our "Memory"
    
    # --- THE RUNNING TOTAL SCROLL ---
    for i in range(20): # More loops for high-volume accounts
        # 1. Scrape IDs currently visible on the screen
        current_content = page.content()
        ids_on_screen = re.findall(r"ID(?:\sPustaka)?:\s?(\d+)", current_content)
        
        # 2. Add them to our permanent set (automatically removes duplicates)
        for ad_id in ids_on_screen:
            all_found_ids.add(ad_id)
        
        print(f"Loop {i}: Total unique ads found so far: {len(all_found_ids)}")

        # 3. Scroll down to trigger the NEXT batch
        page.mouse.wheel(0, 2000) 
        time.sleep(4) # Give Meta time to swap the 30 ads
        
        # 4. Handle the "See More" button if it blocks the scroll
        try:
            btn = page.locator('div[role="button"]:has-text("More"), button:has-text("More"), div[role="button"]:has-text("Lagi")').first
            if btn.is_visible():
                btn.click(force=True)
                time.sleep(3)
        except:
            pass

    # --- FINAL RESULTS ---
    final_count = len(all_found_ids)
    image_path = "snapshot.png"
    # Take a screenshot of the CURRENT view (usually the bottom of the list)
    page.screenshot(path=image_path, full_page=True) 
    
    browser.close()
    return final_count, image_path
    # ---------------------------------------

    # Recount after all scrolling is done
    ad_ids = page.get_by_text(re.compile(r"ID Pustaka:|ID:", re.IGNORECASE)).all()
    count = len(ad_ids)
    
    image_path = "snapshot.png"
    # Use full_page=True to get the giant scrolling image
    page.screenshot(path=image_path, full_page=True) 
    
    browser.close()
    return count, image_path

if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            current_count, img_path = get_ad_data(playwright)
            send_telegram_photo(f"✅ Onecare Spy Report: {current_count} ads.", img_path)
            print("Done!")
        except Exception as e:
            print(f"Error: {e}")
