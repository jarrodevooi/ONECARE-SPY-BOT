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
    # Give the bot a "Phone-like" taller view to trigger more loads
    context = browser.new_context(viewport={"width": 1280, "height": 1000}) 
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    time.sleep(8)

    # --- THE "THUMB FLICK" SIMULATION ---
    for i in range(12): # 12 scrolls should cover ~100+ ads
        # Scroll down 1500 pixels (like a big thumb swipe)
        page.mouse.wheel(0, 1500) 
        time.sleep(3) # CRITICAL: Wait for the "Loading" circle to finish
        
        # Click the "See More" button if it appears
        try:
            # Facebook uses a specific class for that button in 2026
            see_more = page.locator('div[role="button"]:has-text("See More"), div[role="button"]:has-text("Lihat Lagi")').first
            if see_more.is_visible():
                see_more.click(force=True)
                print(f"Scroll {i}: Clicked See More")
                time.sleep(4)
        except:
            pass

    # --- THE "ID" COUNTING TRICK ---
    # We count every unique "ID Pustaka" or "ID:" text found on the long page
    all_text = page.content()
    # This regex finds the pattern of ID numbers Facebook uses
    found_ids = re.findall(r"ID(?:\sPustaka)?:\s?(\d+)", all_text)
    unique_ids = set(found_ids) # Removes any double-counts
    count = len(unique_ids)
    
    image_path = "snapshot.png"
    # Take a "Tall" screenshot of the first 8000 pixels
    page.screenshot(path=image_path, clip={"x": 0, "y": 0, "width": 1280, "height": 8000}) 
    
    browser.close()
    return count, image_path
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
