import os
import time
import requests
from playwright.sync_api import Playwright, sync_playwright

# ENV VARIABLES (set in GitHub Secrets)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TARGET_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=MY&q=onecare&search_type=keyword_unordered&sort_data[mode]=total_impressions&sort_data[direction]=desc"

# Toggle this to debug locally
HEADLESS = True


def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    with open(image_path, "rb") as photo:
        try:
            res = requests.post(
                url,
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"photo": photo},
                timeout=20
            )
            print("Telegram:", res.status_code, res.text)
        except Exception as e:
            print("Telegram Error:", e)


def get_ad_data(playwright: Playwright):
    browser = playwright.chromium.launch(
        headless=HEADLESS,
        args=["--disable-blink-features=AutomationControlled"]
    )

    context = browser.new_context(
        viewport={"width": 1280, "height": 2000},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )

    page = context.new_page()

    try:
        page.goto(TARGET_URL, timeout=90000)

        # Wait for ads to appear
        page.wait_for_selector('[role="article"]', timeout=30000)

        # Scroll to load more ads
        for _ in range(8):
            page.mouse.wheel(0, 5000)
            time.sleep(2)

        # Give extra time to render
        page.wait_for_timeout(3000)

        ads = page.locator('[role="article"]')
        count = ads.count()

        if count == 0:
            print("⚠️ Warning: 0 ads detected — possible block")

        image_path = "snapshot.png"
        page.screenshot(path=image_path, full_page=True)

        browser.close()
        return count, image_path

    except Exception as e:
        print("❌ Error loading page:", e)
        page.screenshot(path="error.png")
        browser.close()
        return 0, "error.png"


if __name__ == "__main__":
    with sync_playwright() as playwright:
        try:
            current_count, img_path = get_ad_data(playwright)

            caption = f"✅ OneCare Spy Report\nAds detected: {current_count}"

            send_telegram_photo(caption, img_path)

            print("✅ Done!")

        except Exception as e:
            print(f"❌ Fatal Error: {e}")
