import os
import re
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import expect

load_dotenv()

STATE = Path("secrets/auth_state.json")
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "5009")
PROJECT_URL = "https://rhombusai.com/workflow/" + PROJECT_ID


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    if not STATE.exists():
        pytest.skip("secrets/auth_state.json is missing (see the README: run ui-tests/save_login_cdp.py)")
    return {**browser_context_args, "storage_state": str(STATE), "viewport": {"width": 1600, "height": 900}}


def open_project(page):
    # The 'Ad Blocker Detected' modal can appear at any moment. This handler clicks it away
    # whenever it shows up, so no test needs a fixed sleep to wait for it.
    page.add_locator_handler(
        page.get_by_role("button", name=re.compile("continue anyway", re.I)),
        lambda button: button.click(),
    )
    page.goto(PROJECT_URL)
    if "/workflow/" not in page.url:
        pytest.fail(
            "The saved login session was rejected (landed on " + page.url.split("?")[0] + "). "
            "Run ui-tests/save_login_cdp.py again.",
            pytrace=False,
        )
    expect(page.get_by_role("tab", name="Canvas")).to_be_visible(timeout=30000)


@pytest.fixture
def project_page(page):
    open_project(page)
    return page
