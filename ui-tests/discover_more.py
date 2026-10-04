import os
import re
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "5009")
URL = "https://rhombusai.com/workflow/" + PROJECT_ID
REPORT = Path("/tmp/ui-discovery2.txt")  # outside the repo on purpose
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
        out("failed: " + type(error).__name__ + " " + str(error)[:150])


ICONS_JS = """() => Array.from(document.querySelectorAll('button'))
  .filter(b => b.offsetParent !== null).slice(0, 40).map(b => {
    const svg = b.querySelector('svg');
    const r = b.getBoundingClientRect();
    return {text: (b.innerText || '').trim().slice(0, 25), aria: b.getAttribute('aria-label') || '',
            title: b.getAttribute('title') || '', icon: svg ? (svg.getAttribute('class') || '') : '',
            x: Math.round(r.x), y: Math.round(r.y)};
  })"""


def sidebar_text(page, limit=1500):
    out(page.get_by_test_id("right-sidebar").inner_text()[:limit])


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state="secrets/auth_state.json", viewport={"width": 1600, "height": 900})
    page = context.new_page()
    page.add_locator_handler(page.get_by_role("button", name=re.compile("continue anyway", re.I)),
                             lambda b: b.click())
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector(".react-flow__node", timeout=30000)

    def toolbar():
        for row in page.evaluate(ICONS_JS):
            if row["icon"] or row["text"] or row["aria"] or row["title"]:
                out("  " + str(row))
    section("buttons with their icon classes, text and positions", toolbar)

    def controls():
        out("react-flow controls buttons: " + str(page.locator(".react-flow__controls button").count()))
        out("minimap present: " + str(page.locator(".react-flow__minimap").count()))
        for i in range(page.locator(".react-flow__controls button").count()):
            b = page.locator(".react-flow__controls button").nth(i)
            out("  controls button " + str(i) + " class=" + str(b.get_attribute("class")) + " aria=" + str(b.get_attribute("aria-label")))
    section("canvas controls", controls)

    def zoom_out():
        box = page.locator(".react-flow").first.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        for modifier in (None, "Control"):
            if modifier:
                page.keyboard.down(modifier)
            for _ in range(5):
                page.mouse.wheel(0, 400)
            if modifier:
                page.keyboard.up(modifier)
            page.wait_for_timeout(1000)  # discovery only; real tests must not use fixed sleeps
            ids = page.locator(".react-flow__node").evaluate_all("els => els.map(e => e.getAttribute('data-id'))")
            out("after zoom attempt (" + str(modifier) + "): " + str(len(ids)) + " nodes: " + str(ids))
            if len(ids) >= 10:
                break
    section("zoomed-out node ids", zoom_out)

    for name in ["Data Input", "Data Output"]:
        def read_node(name=name):
            page.locator(".react-flow__node", has_text=name).first.click(timeout=8000)
            page.wait_for_timeout(1500)
            sidebar_text(page)
        section("sidebar after clicking the " + name + " node", read_node)

    def add_schedule():
        page.get_by_role("tab", name="Schedule").click()
        page.get_by_role("button", name="Add Schedule").click()
        page.wait_for_timeout(1500)
        out("dialogs: " + str(page.locator("[role=dialog]").count()))
        if page.locator("[role=dialog]").count():
            out(page.locator("[role=dialog]").first.inner_text()[:800])
        page.keyboard.press("Escape")
    section("Add Schedule dialog (closed again with Escape, nothing saved)", add_schedule)

    def schedule_card():
        page.get_by_role("tab", name="Schedule").click()
        sidebar_text(page, 600)
    section("schedule card text", schedule_card)

    def project_menu():
        page.get_by_test_id("project-actions").first.click()
        page.wait_for_timeout(1000)
        menus = page.locator("[role=menu]")
        out("menus: " + str(menus.count()))
        if menus.count():
            out(menus.first.inner_text()[:400])
        page.keyboard.press("Escape")
    section("project actions menu (read only, closed with Escape)", project_menu)

    def dashboard():
        page.get_by_role("button", name="Dashboard").click()
        page.wait_for_selector("text=Executions", timeout=15000)
        out(page.locator("main").first.inner_text()[:1500])
        for tab in ["Executions", "Schedules"]:
            try:
                page.get_by_role("tab", name=tab).first.click(timeout=3000)
                page.wait_for_timeout(1500)
                out("--- " + tab + " tab ---")
                out(page.locator("main").first.inner_text()[:900])
            except Exception as error:
                out("tab " + tab + " not clicked: " + type(error).__name__)
    section("dashboard", dashboard)

    browser.close()

REPORT.write_text("\n".join(lines) + "\n")
print()
print("full report saved to", REPORT)
