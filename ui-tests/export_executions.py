import csv
from pathlib import Path

from playwright.sync_api import sync_playwright

from ui_helpers import STATE, dismiss_ad_blocker_modal, open_dashboard, read_execution_rows

OUT = Path("datasets/rhombus_executions.csv")

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state=str(STATE), viewport={"width": 1600, "height": 1000})
    page = context.new_page()
    dismiss_ad_blocker_modal(page)
    open_dashboard(page)
    seen = {}
    for page_no in range(1, 15):
        for row in read_execution_rows(page):
            seen[row["number"]] = row
        print("page", page_no, "- executions collected so far:", len(seen))
        # the last four buttons on the page should be first, previous, next, last
        buttons = page.locator("button").all()
        nxt = buttons[-2] if len(buttons) >= 4 else None
        if nxt is None or not nxt.is_enabled():
            break
        first_before = page.locator("tbody tr").first.inner_text()
        nxt.click()
        page.wait_for_function("t => document.querySelector('tbody tr') && "
                               "document.querySelector('tbody tr').innerText !== t", arg=first_before, timeout=10000)
    rows = [seen[n] for n in sorted(seen, reverse=True)]
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["number", "trigger", "project", "started", "duration_s", "status", "nodes"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote", len(rows), "executions to", OUT)
    browser.close()
