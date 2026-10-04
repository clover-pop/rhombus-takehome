import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from ui_helpers import PROJECT_URL, STATE, dismiss_ad_blocker_modal

REPORT = Path("/tmp/ui-discovery6.txt")  # outside the repo on purpose
BLOCKED = re.compile(r"connect|create|apply|save|delete|remove|run", re.I)
POPUPS = "[role=menu], [role=dialog], [role=listbox], [data-radix-popper-content-wrapper]"
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


def safe_click(locator):
    text = (locator.inner_text() or "").strip()
    if BLOCKED.search(text):
        raise RuntimeError("refusing to click '" + text + "'")
    locator.click()


def clear_banner(page):
    button = page.get_by_role("button", name=re.compile("continue anyway", re.I))
    if button.count() and button.first.is_visible():
        button.first.click()
        page.wait_for_timeout(500)  # discovery only; the real tests wait on conditions instead


def dump(page):
    clear_banner(page)
    found = page.locator(POPUPS)
    out("popups: " + str(found.count()))
    for i in range(min(found.count(), 3)):
        out("  popup " + str(i) + ": " + found.nth(i).inner_text().replace("\n", " | ")[:700])
    for b in page.locator("[role=dialog] button, [role=menu] button, [role=menuitem]").all()[:15]:
        out("  control: " + b.inner_text().strip().replace("\n", " ")[:40] + " | disabled=" + str(b.is_disabled()))
    for i in page.locator("[role=dialog] input, [role=dialog] textarea").all()[:8]:
        out("  input: placeholder=" + str(i.get_attribute("placeholder")) + " | name=" + str(i.get_attribute("name")))


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state=str(STATE), viewport={"width": 3400, "height": 1000})
    page = context.new_page()
    dismiss_ad_blocker_modal(page)

    def open_existing():
        page.goto(PROJECT_URL, wait_until="domcontentloaded")
        page.wait_for_function("document.querySelectorAll('.react-flow__node').length >= 10", timeout=30000)

    def throwaway():
        open_existing()
        page.get_by_test_id("project-card").filter(has_text="throwaway").click()
        page.wait_for_function("u => location.href !== u", arg=PROJECT_URL, timeout=20000)
        out("throwaway url: " + page.url.split("?")[0])
        page.get_by_role("tab", name="Canvas").wait_for(timeout=20000)
        sidebar = page.get_by_test_id("right-sidebar")
        for t in sidebar.locator("textarea").all()[:2]:
            out("chat input placeholder: " + str(t.get_attribute("placeholder")))
    section("the throwaway project", throwaway)

    def canvas_plus():
        page.locator('button:has(svg[class*="lucide-plus"][class*="h-[18px]"])').first.click()
        page.wait_for_timeout(1500)
        dump(page)
        page.keyboard.press("Escape")
    section("the canvas + button", canvas_plus)

    def chat_plus():
        sidebar = page.get_by_test_id("right-sidebar")
        sidebar.locator('button:has(svg[class*="lucide-plus"])').first.click()
        page.wait_for_timeout(1500)
        dump(page)
        page.keyboard.press("Escape")
    section("the chat attach + button", chat_plus)

    def s3_form():
        open_existing()
        page.locator('.react-flow__node[data-id="input_node_1"]').click()
        page.get_by_text("Third Party Sources").click()
        clear_banner(page)
        safe_click(page.get_by_role("button", name="Add Data Sources").first)
        page.wait_for_timeout(1500)
        out("--- provider list ---")
        dump(page)
        page.get_by_text(re.compile(r"^\s*Amazon S3\s*$")).last.click()
        page.get_by_text(re.compile(r"^Bucket")).first.wait_for(timeout=30000)
        out("--- the S3 form, after it finished loading (not submitted) ---")
        dump(page)
        for label in ("Connect S3 source", "Back to Data Sources", "Cancel"):
            b = page.get_by_role("button", name=label)
            if b.count():
                out("  button '" + label + "' disabled=" + str(b.first.is_disabled()))
        page.keyboard.press("Escape")
    section("the S3 form (not submitted)", s3_form)

    def browse_files():
        open_existing()
        page.locator('.react-flow__node[data-id="input_node_1"]').click()
        page.get_by_text("Third Party Sources").click()
        clear_banner(page)
        safe_click(page.get_by_role("button", name="Browse files").first)
        page.wait_for_timeout(3000)
        dump(page)
        page.keyboard.press("Escape")
    section("Browse files on the connected source", browse_files)

    def gcs_form():
        open_existing()
        page.locator(".react-flow__node", has_text="Data Output").first.click()
        safe_click(page.get_by_text("Add New Destination").first)
        page.get_by_text("Google Cloud Storage", exact=True).first.click()
        page.wait_for_timeout(3000)
        dump(page)
        page.keyboard.press("Escape")
    section("the Google Cloud Storage destination form (not submitted)", gcs_form)

    browser.close()

REPORT.write_text("\n".join(lines) + "\n")
print()
print("full report saved to", REPORT)
