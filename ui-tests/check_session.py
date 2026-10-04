import sys

from playwright.sync_api import sync_playwright

url = sys.argv[1]
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state="secrets/auth_state.json")
    page = context.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    print("landed on:", page.url.split("?")[0])
    print("title:", page.title())
    page.screenshot(path="/tmp/ui-session-check.png")
    browser.close()
