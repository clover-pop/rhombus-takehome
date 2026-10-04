import os
import re
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "5009")
URL = "https://rhombusai.com/workflow/" + PROJECT_ID
STATE = "secrets/auth_state.json"
REPORT = Path("/tmp/ui-discovery.txt")  # outside the repo on purpose

lines = []


def out(text=""):
    text = re.sub(r"\S+@\S+", "<email>", str(text))
    print(text)
    lines.append(text)


LIST_JS = r"""() => {
  const sel = 'button, [role=tab], [role=button], [role=dialog], [role=switch], [data-testid], input, textarea';
  return Array.from(document.querySelectorAll(sel))
    .filter(e => e.offsetParent !== null)
    .slice(0, 80)
    .map(e => ({
      tag: e.tagName.toLowerCase(),
      role: e.getAttribute('role') || '',
      text: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40),
      aria: e.getAttribute('aria-label') || '',
      testid: e.getAttribute('data-testid') || '',
      placeholder: e.getAttribute('placeholder') || ''
    }));
}"""


def describe(page, label):
    out()
    out("=== " + label + " ===")
    out("url: " + page.url.split("?")[0])
    nodes = page.locator(".react-flow__node")
    out("canvas nodes (.react-flow__node): " + str(nodes.count()))
    for i in range(min(nodes.count(), 20)):
        n = nodes.nth(i)
        out("  node data-id=" + str(n.get_attribute("data-id")) + " | " + (n.inner_text() or "").replace("\n", " / ")[:60])
    for row in page.evaluate(LIST_JS):
        parts = [row["tag"]]
        for key in ("role", "text", "aria", "testid", "placeholder"):
            if row[key]:
                parts.append(key + "=" + row[key])
        out("  " + " | ".join(parts))


def dismiss_banner(page):
    button = page.get_by_role("button", name=re.compile("continue anyway", re.I))
    try:
        button.first.wait_for(state="visible", timeout=5000)
        out("ad blocker banner found; button text: " + button.first.inner_text().strip())
        button.first.click()
    except Exception:
        out("no 'continue anyway' button found")


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(storage_state=STATE, viewport={"width": 1600, "height": 900})
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(".react-flow__node", timeout=20000)
    except Exception:
        out("no .react-flow__node appeared within 20 seconds")
    describe(page, "before dismissing the banner")
    dismiss_banner(page)
    describe(page, "project page after the banner")

    for tab in ["Canvas", "Workspace", "Preview", "Logs", "AI Builder", "Schedule", "Transform", "Profile"]:
        try:
            page.get_by_text(tab, exact=True).first.click(timeout=3000)
            page.wait_for_timeout(1500)  # discovery only; the real tests must not use fixed sleeps
            describe(page, "after clicking the " + tab + " tab")
        except Exception as error:
            out()
            out("=== tab " + tab + " could not be clicked: " + type(error).__name__ + " ===")

    for node_text in ["Data Input", "Data Output"]:
        try:
            page.get_by_text("Canvas", exact=True).first.click(timeout=3000)
            page.locator(".react-flow__node", has_text=node_text).first.click(timeout=5000)
            page.wait_for_timeout(1500)
            describe(page, "after clicking the " + node_text + " node")
        except Exception as error:
            out()
            out("=== node " + node_text + " could not be clicked: " + type(error).__name__ + " ===")

    page.screenshot(path="/tmp/ui-discovery.png")
    browser.close()

REPORT.write_text("\n".join(lines) + "\n")
print()
print("full report saved to", REPORT)
