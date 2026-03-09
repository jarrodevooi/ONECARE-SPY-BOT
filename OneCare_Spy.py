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
    context = browser.new_context(viewport={"width": 1280, "height": 2000})
    page = context.new_page()
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7) 
    
    ad_ids = page.get_by_text(re.compile(r"ID Pustaka:|ID:", re.IGNORECASE)).all()
    count = len(ad_ids)
    
    image_path = "snapshot.png"
    page.screenshot(path=image_path)
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
