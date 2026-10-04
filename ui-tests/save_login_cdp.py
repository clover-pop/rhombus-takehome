from pathlib import Path

from playwright.sync_api import sync_playwright

STATE = Path("secrets/auth_state.json")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0]
    print("open pages:", [page.url.split("?")[0] for page in context.pages])
    STATE.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(STATE))
    print("saved", STATE)
