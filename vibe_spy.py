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
    # Set a very tall initial viewport to encourage loading
    context = browser.new_context(viewport={"width": 1280, "height": 5000}) 
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    time.sleep(5)

    # --- AGGRESSIVE SCROLL & BUTTON HUNT ---
    for i in range(10):  # Try 10 times to find more ads
        # 1. Scroll to the bottom of the page
        page.mouse.wheel(0, 15000) 
        time.sleep(4)
        
        # 2. Find and click ANY button that looks like "See More"
        try:
            # This looks for buttons OR divs that contain the 'more' text
            see_more = page.locator('div[role="button"]:has-text("More"), button:has-text("More"), div[role="button"]:has-text("Lagi")').first
            if see_more.is_visible():
                see_more.click(force=True)
                print(f"Action: Clicked 'See More' on loop {i}")
                time.sleep(5) # Give it time to actually fetch new ads
            else:
                # If no button, try one last scroll
                page.keyboard.press("End")
        except:
            page.keyboard.press("End")
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
