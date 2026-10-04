import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from ui_helpers import PROJECT_URL, STATE, dismiss_ad_blocker_modal

REPORT = Path("/tmp/ui-discovery5.txt")  # outside the repo on purpose
BLOCKED = re.compile(r"connect|create|apply|save|delete|remove|run", re.I)
lines = []


def out(text=""):
    text = re.sub(r"\S+@\S+", "<email>", str(text))
    print(text)
    lines.append(text)


def safe_click(locator, label):
    text = (locator.inner_text() or "").strip()
    if BLOCKED.search(text) and label != "Add Data Sources" and label != "Add New Destination":
        raise RuntimeError("refusing to click '" + text + "'")
    locator.click()


def section(label, fn):
    out()
    out("=== " + label + " ===")
    try:
        fn()
    except Exception as error:
        out("failed: " + type(error).__name__ + " " + str(error)[:250])


def dump_dialogs(page):
    dialogs = page.locator("[role=dialog]")
    out("dialogs: " + str(dialogs.count()))
    if dialogs.count():
        out(dialogs.last.inner_text()[:1200])
    for b in page.locator("[role=dialog] button").all()[:15]:
        out("  button: text=" + b.inner_text().strip()[:40] + " | disabled=" + str(b.is_disabled()))
    for i in page.locator("[role=dialog] input").all()[:6]:
        out("  input: placeholder=" + str(i.get_attribute("placeholder")) + " | name=" + str(i.get_attribute("name")))


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state=str(STATE), viewport={"width": 3400, "height": 1000})
    page = context.new_page()
    dismiss_ad_blocker_modal(page)

    def fresh():
        page.goto(PROJECT_URL, wait_until="domcontentloaded")
        page.wait_for_function("document.querySelectorAll('.react-flow__node').length >= 10", timeout=30000)

    def add_source():
        fresh()
        page.locator('.react-flow__node[data-id="input_node_1"]').click()
        page.get_by_text("Third Party Sources").click()
        safe_click(page.get_by_role("button", name="Add Data Sources").first, "Add Data Sources")
        page.wait_for_timeout(1500)  # discovery only; the real tests wait on conditions instead
        dump_dialogs(page)
    section("Add Data Sources", add_source)

    def s3_form():
        tile = page.get_by_text(re.compile(r"^\s*Amazon S3\s*$")).last
        out("tile text: " + tile.inner_text())
        tile.click()
        page.wait_for_timeout(1500)
        dump_dialogs(page)
    section("the S3 form (not submitted)", s3_form)

    def add_destination():
        fresh()
        page.locator(".react-flow__node", has_text="Data Output").first.click()
        safe_click(page.get_by_text("Add New Destination").first, "Add New Destination")
        page.wait_for_timeout(1500)
        dump_dialogs(page)
        out("sidebar: " + page.get_by_test_id("right-sidebar").inner_text()[:800])
    section("Add New Destination", add_destination)

    browser.close()

REPORT.write_text("\n".join(lines) + "\n")
print()
print("full report saved to", REPORT)
