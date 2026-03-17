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

        time.sleep(5)

        page.mouse.move(100, 100)
        page.click("body")

        page.wait_for_selector('div[role="article"]', timeout=30000)

        for _ in range(8):
            page.mouse.wheel(0, 5000)
            time.sleep(2)

        page.wait_for_timeout(3000)

    count = 0

try:
    # Get all visible text on the page
    body_text = page.locator("body").inner_text()

    import re
    # Look for a number followed by 'results' anywhere in the text
    match = re.search(r"(\d{2,4})\s*results", body_text.lower())

    if match:
        count = int(match.group(1))
    else:
        print("⚠️ Could not find results text, falling back...")

except Exception as e:
    print("Error extracting results:", e)

# Fallback if still 0
if count == 0:
    ads1 = page.locator('div[data-ad-preview="message"]')
    ads2 = page.locator('div[role="article"]')
    count = max(ads1.count(), ads2.count())

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
