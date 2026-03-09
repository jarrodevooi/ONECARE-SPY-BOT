import os
import re
import time
import requests
from playwright.sync_api import Playwright, sync_playwright

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- FIX 1: USE THE OFFICIAL PAGE ID URL ---
# This ensures you see the REAL brand ads, not just keyword matches
TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&view_all_page_id=141890315998188&sort_data[mode]=total_impressions&sort_data[direction]=desc"

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900}) 
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    time.sleep(7)

    all_found_ids = set() # This is your 'Memory' to beat the 30-ad limit
    
    # --- FIX 2: THE MEMORY LOOP ---
    for i in range(15): 
        # 1. Grab IDs currently on screen before Meta deletes them
        current_content = page.content()
        ids_on_screen = re.findall(r"ID(?:\sPustaka)?:\s?(\d+)", current_content)
        
        for ad_id in ids_on_screen:
            all_found_ids.add(ad_id)
        
        print(f"Loop {i}: Found {len(all_found_ids)} unique ads so far...")

        # 2. Scroll and click to trigger more ads
        page.mouse.wheel(0, 2000) 
        time.sleep(4)
        
        try:
            btn = page.locator('div[role="button"]:has-text("More"), button:has-text("More"), div[role="button"]:has-text("Lagi")').first
            if btn.is_visible():
                btn.click(force=True)
                time.sleep(3)
        except:
            pass

    # Final result using your collected memory
    final_count = len(all_found_ids)
    image_path = "snapshot.png"
    page.screenshot(path=image_path, full_page=True) 
    
    browser.close()
    return final_count, image_path

if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            current_count, img_path = get_ad_data(playwright)
            send_telegram_photo(f"✅ Onecare Spy Report: {current_count} ads found.", img_path)
            print(f"Done! Final count: {current_count}")
        except Exception as e:
            print(f"Error: {e}")
