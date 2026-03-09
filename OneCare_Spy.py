import re
import time
import requests
from playwright.sync_api import Playwright, sync_playwright

# --- CONFIGURATION ---
TOKEN = "8440176825:AAHICj33jCSdjlxRKB_VjHcSzeZKFSJ05Ec" # <--- Put your token here
CHAT_ID = "1294111764"
TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&q=onecare&search_type=keyword_unordered&sort_data[mode]=total_impressions&sort_data[direction]=desc"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 2000},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    print("Opening Onecare Ad Library...")
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)
    
    # Give it a moment to settle
    time.sleep(5)
    page.keyboard.press("Escape")

    print("Scrolling to capture all active ads...")
    for _ in range(4):
        page.mouse.wheel(0, 1000)
        time.sleep(1.5)

    # NEW LOGIC: Count the unique Ad ID labels (ID Pustaka) 
    # This works in both English and Malay
    print("Counting ads by ID labels...")
    ad_ids = page.get_by_text(re.compile(r"ID Pustaka:|ID:", re.IGNORECASE)).all()
    count = len(ad_ids)
    
    image_path = "onecare_snapshot.png"
    # Capture a large area so you can see the designs in Telegram
    page.screenshot(path=image_path, full_page=False)
    
    print(f"Final Count Found: {count}")
    context.close()
    browser.close()
    return count, image_path
def start_monitoring():
    last_count = -1
    print("Bot is alive and watching Onecare...")

    with sync_playwright() as playwright:
        while True:
            try:
                current_count, img_path = get_ad_data(playwright)
                
                if last_count != -1 and current_count != last_count:
                    diff = current_count - last_count
                    status = "launched NEW ads! 🚀" if diff > 0 else "removed ads. 📉"
                    caption = f"🚨 ONECARE UPDATE: They {status}\nNow: {current_count} ads."
                    send_telegram_photo(caption, img_path)
                
                elif last_count == -1:
                    send_telegram_msg(f"✅ Bot Active. Onecare currently has {current_count} ads.")

                last_count = current_count
            except Exception as e:
                print(f"Error: {e}")
            
            # Check every 4 hours
            time.sleep(14400)

if __name__ == "__main__":
    start_monitoring()