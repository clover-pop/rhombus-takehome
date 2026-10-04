import os
import re
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "5009")
URL = "https://rhombusai.com/workflow/" + PROJECT_ID
REPORT = Path("/tmp/ui-discovery3.txt")  # outside the repo on purpose
lines = []

NODES_JS = """() => Array.from(document.querySelectorAll('.react-flow__node'))
  .map(e => e.getAttribute('data-id') + ' | ' + (e.innerText || '').replace(/\\s+/g, ' ').slice(0, 50))"""


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
        out("failed: " + type(error).__name__ + " " + str(error)[:200])


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state="secrets/auth_state.json",
                                  viewport={"width": 3400, "height": 1000})
    page = context.new_page()
    page.add_locator_handler(page.get_by_role("button", name=re.compile("continue anyway", re.I)),
                             lambda b: b.click())
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector(".react-flow__node", timeout=30000)
    seen = {}

    def snapshot():
        for row in page.evaluate(NODES_JS):
            seen[row.split(" | ")[0]] = row

    def drag(dx):
        box = page.locator(".react-flow__pane").first.bounding_box()
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] - 30
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + dx, y, steps=12)
        page.mouse.up()
        page.wait_for_timeout(600)  # discovery only; real tests must not use fixed sleeps

    def reveal(text):
        if page.locator(".react-flow__node", has_text=text).count():
            return True
        for dx, steps in ((500, 8), (-500, 20)):
            for _ in range(steps):
                drag(dx)
                snapshot()
                if page.locator(".react-flow__node", has_text=text).count():
                    return True
        return False

    def wide():
        snapshot()
        out("viewport style: " + str(page.locator(".react-flow__viewport").first.get_attribute("style")))
        out("nodes rendered at 3400px wide: " + str(len(seen)))
        for row in seen.values():
            out("  " + row)
    section("nodes at a very wide window", wide)

    def pan_all():
        reveal("zzz-never-matches")
        out("distinct nodes seen while panning: " + str(len(seen)))
        for row in sorted(seen.values()):
            out("  " + row)
    section("nodes found by dragging the canvas", pan_all)

    for name in ["Data Input", "Data Output"]:
        def read_node(name=name):
            found = reveal(name)
            out("node visible after panning: " + str(found))
            page.locator(".react-flow__node", has_text=name).first.click(timeout=8000)
            page.wait_for_timeout(1500)
            out(page.get_by_test_id("right-sidebar").inner_text()[:1800])
        section("right sidebar after clicking the " + name + " node", read_node)

    def workspace():
        page.get_by_role("tab", name="Workspace").click()
        page.wait_for_timeout(1500)
        out(page.locator("body").inner_text()[:1200])
        page.get_by_role("tab", name="Canvas").click()
    section("Workspace tab", workspace)

    def dashboard():
        page.get_by_role("button", name="Dashboard").click()
        page.wait_for_selector("text=Executions", timeout=15000)
        out("url: " + page.url.split("?")[0])
        out(page.locator("body").inner_text()[:700])
        page.locator("button:has-text('Executions')").first.click()
        page.wait_for_timeout(2000)
        out("tables: " + str(page.locator("table").count())
            + " | tr rows: " + str(page.locator("tr").count())
            + " | role=row: " + str(page.locator("[role=row]").count()))
        rows = page.locator("tr")
        if rows.count() == 0:
            rows = page.locator("[role=row]")
        for i in range(min(rows.count(), 6)):
            out("  row " + str(i) + ": " + rows.nth(i).inner_text().replace("\n", " | ")[:160])
    section("dashboard, Executions tab", dashboard)

    browser.close()

REPORT.write_text("\n".join(lines) + "\n")
print()
print("full report saved to", REPORT)
