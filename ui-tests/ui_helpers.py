import os
import re
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import expect

load_dotenv()

STATE = Path("secrets/auth_state.json")
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "5009")
PROJECT_URL = "https://rhombusai.com/workflow/" + PROJECT_ID
DASHBOARD_URL = "https://rhombusai.com/dashboard"

ROW_RE = re.compile(
    r"Execution #(\d+)\s+(\w+)\s+(\S+)\s+(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}:\d{2} [AP]M)"
    r"\s+([\d.]+)s\s+(Success|Failure)\s+(\d+ nodes|\u2014)"
)


def dismiss_ad_blocker_modal(page):
    # The 'Ad Blocker Detected' modal can appear at any moment. This handler clicks it away whenever
    # it shows up, so no test needs a fixed sleep to wait for it.
    page.add_locator_handler(
        page.get_by_role("button", name=re.compile("continue anyway", re.I)),
        lambda button: button.click(),
    )


def open_project(page):
    page.goto(PROJECT_URL)
    if "/workflow/" not in page.url:
        pytest.fail("The saved login session was rejected (landed on " + page.url.split("?")[0]
                    + "). Run ui-tests/save_login_cdp.py again.", pytrace=False)
    expect(page.get_by_role("tab", name="Canvas")).to_be_visible(timeout=30000)


def open_dashboard(page):
    page.goto(DASHBOARD_URL)
    if "/dashboard" not in page.url:
        pytest.fail("The saved login session was rejected (landed on " + page.url.split("?")[0] + ").",
                    pytrace=False)
    page.locator("button:has-text('Executions')").first.click()
    expect(page.locator("tbody tr").first).to_contain_text("Execution #", timeout=30000)


def read_execution_rows(page):
    texts = page.locator("tbody tr").evaluate_all("rows => rows.map(r => r.innerText)")
    rows = []
    for text in texts:
        m = ROW_RE.search(text)
        assert m, "unexpected row layout: " + repr(text[:150])
        rows.append({"number": int(m.group(1)), "trigger": m.group(2), "project": m.group(3),
                     "started": m.group(4), "duration_s": float(m.group(5)),
                     "status": m.group(6), "nodes": m.group(7)})
    return rows


def poll_until(fn, timeout_s, interval_s, what):
    """Bounded wait on a real condition (used for external systems like GCS, not a fixed sleep)."""
    deadline = time.monotonic() + timeout_s
    while True:
        value = fn()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise AssertionError("timed out after " + str(timeout_s) + "s waiting for " + what)
        time.sleep(interval_s)
