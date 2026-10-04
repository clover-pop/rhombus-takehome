import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

STATE = Path("secrets/auth_state.json")
START_URL = "https://rhombusai.com/"
channel = "chrome" if "chrome" in sys.argv[1:] else None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel=channel)
    context = browser.new_context()
    page = context.new_page()
    page.goto(START_URL)
    print("Log in to Rhombus in the browser window and open your project page.")
    print("Then come back here and press Enter to save the session.")
    input()
    STATE.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(STATE))
    print("saved", STATE)
    browser.close()
