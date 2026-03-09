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
    # Using a taller viewport to trigger more initial ads
    context = browser.new_context(viewport={"width": 1280, "height": 1200})
    page = context.new_page()

    all_found_ids = set()

    # 1. Go to the Page ID link
    page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
    
    # 2. CRITICAL: Wait for the OneCare profile header to actually exist
    # This prevents the '0 ads' error by making sure the page isn't blank
    try:
        page.wait_for_selector('div[role="main"]', timeout=20000)
        time.sleep(5) 
    except:
        print("Page took too long to load, attempting to scroll anyway...")

    # --- THE VISUAL MEMORY LOOP ---
    for i in range(15):
        # Scrape IDs currently visible in the HTML
        content = page.content()
        # Facebook Ad IDs are 15-16 digits
        ids_on_screen = re.findall(r"ID(?:\sPustaka)?:\s?(\d{15,16})", content)
        
        for ad_id in ids_on_screen:
            all_found_ids.add(ad_id)
        
        print(f"Scroll {i}: Unique ads in memory: {len(all_found_ids)}")

        # Human-like scroll
        page.mouse.wheel(0, 2000)
        time.sleep(4)
        
        # Handle the 'See More' / 'Lagi' button
        try:
            btn = page.locator('div[role="button"]:has-text("More"), button:has-text("More"), div[role="button"]:has-text("Lagi")').first
            if btn.is_visible():
                btn.click(force=True)
                time.sleep(4)
        except:
            pass

    count = len(all_found_ids)
    
    # Final Fallback: If memory is still 0, count the "Active" status labels
    if count == 0:
        badges = page.get_by_text(re.compile(r"Active|Aktif", re.IGNORECASE)).all()
        count = len(badges)

    image_path = "snapshot.png"
    # Screenshot of the page showing the ads (not a blank search bar)
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
