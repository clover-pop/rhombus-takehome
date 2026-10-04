import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from ui_helpers import PROJECT_URL, STATE, dismiss_ad_blocker_modal

REPORT = Path("/tmp/ui-discovery4.txt")  # outside the repo on purpose
lines = []


def out(text=""):
    text = re.sub(r"\S+@\S+", "<email>", str(text))
    print(text)
    lines.append(text)


def section(label, fn):
    out()
    out("=== " + label + " ===")
    try:
        fn()
    except Exception as error:
        out("failed: " + type(error).__name__ + " " + str(error)[:250])


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state=str(STATE), viewport={"width": 3400, "height": 1000})
    page = context.new_page()
    dismiss_ad_blocker_modal(page)
    page.goto(PROJECT_URL, wait_until="domcontentloaded")
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_function("document.querySelectorAll('.react-flow__node').length >= 10", timeout=30000)
    sidebar = page.get_by_test_id("right-sidebar")

    def data_input():
        page.locator('.react-flow__node[data-id="input_node_1"]').click()
        page.wait_for_timeout(1500)  # discovery only; the real tests wait on conditions instead
        out(sidebar.inner_text()[:1800])
    section("Data Input panel", data_input)

    def third_party():
        page.get_by_text("Third Party Sources").first.click()
        page.wait_for_timeout(1500)
        out("dialogs: " + str(page.locator("[role=dialog]").count()))
        target = page.locator("[role=dialog]").first if page.locator("[role=dialog]").count() else sidebar
        out(target.inner_text()[:1500])
    section("after clicking Third Party Sources", third_party)

    def s3_form():
        option = page.get_by_text(re.compile(r"s3", re.I)).first
        out("s3 option text: " + option.inner_text()[:80])
        option.click()
        page.wait_for_timeout(1500)
        target = page.locator("[role=dialog]").first if page.locator("[role=dialog]").count() else sidebar
        out(target.inner_text()[:1500])
        for b in page.locator("[role=dialog] button").all()[:12]:
            out("  button: text=" + b.inner_text().strip()[:40] + " | disabled=" + str(b.is_disabled()))
        for i in page.locator("[role=dialog] input").all()[:6]:
            out("  input: placeholder=" + str(i.get_attribute("placeholder")) + " | name=" + str(i.get_attribute("name")))
    section("S3 connection form (not submitted)", s3_form)
    page.keyboard.press("Escape")

    def data_output():
        page.goto(PROJECT_URL, wait_until="domcontentloaded")
        page.wait_for_function("document.querySelectorAll('.react-flow__node').length >= 10", timeout=30000)
        page.locator(".react-flow__node", has_text="Data Output").first.click()
        page.wait_for_timeout(1500)
        out(page.get_by_test_id("right-sidebar").inner_text()[:2200])
    section("Data Output panel", data_output)

    browser.close()

REPORT.write_text("\n".join(lines) + "\n")
print()
print("full report saved to", REPORT)
