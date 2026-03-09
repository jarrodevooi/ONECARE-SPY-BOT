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
    # 1. Use a Mobile Device Profile
    iphone = playwright.devices['iPhone 13']
    browser = playwright.chromium.launch(headless=True)
    
    # 2. Set the context to mimic a real mobile phone
    context = browser.new_context(
        **iphone,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    )
    
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    time.sleep(8)

    # --- MOBILE SCROLL LOOP ---
    for i in range(15): 
        # Mimic a thumb flick (scroll down 1200 pixels)
        page.mouse.wheel(0, 1200) 
        time.sleep(3) 
        
        # Mobile often has a "Load More" button instead of "See More"
        try:
            load_more = page.get_by_role("button", name=re.compile(r"Load|More|Lagi", re.IGNORECASE)).first
            if load_more.is_visible():
                load_more.click(force=True)
                print(f"Mobile Loop {i}: Tapped Load More")
                time.sleep(4)
        except:
            pass

    # --- ACCURATE MOBILE COUNT ---
    # Scrape all unique Ad IDs from the mobile source code
    all_content = page.content()
    found_ids = re.findall(r"ID(?:\sPustaka)?:\s?(\d+)", all_content)
    unique_ids = set(found_ids)
    count = len(unique_ids)
    
    # Take a tall screenshot that looks like a phone screen
    image_path = "snapshot.png"
    page.screenshot(path=image_path, clip={"x": 0, "y": 0, "width": 390, "height": 5000}) 
    
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
