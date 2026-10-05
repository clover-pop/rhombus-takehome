import re

from playwright.sync_api import expect


def test_project_opens_with_the_expected_tabs(project_page):
    page = project_page
    for name in ["Canvas", "Workspace", "AI Builder", "Schedule"]:
        expect(page.get_by_role("tab", name=name)).to_be_visible()
    expect(page.get_by_role("button", name="Dashboard")).to_be_visible()
    # The sidebar lists every project, so pick the card for this project and check it is the active one.
    card = page.get_by_test_id("project-card").filter(has_text="rhombus-takehome")
    expect(card).to_have_count(1)
    expect(card).to_have_class(re.compile(r"project-sidebar-control-active"))


def test_canvas_renders_pipeline_nodes_and_edges(project_page):
    page = project_page
    nodes = page.locator(".react-flow__node")
    expect(nodes.first).to_be_visible(timeout=20000)
    ids = nodes.evaluate_all("els => els.map(e => e.getAttribute('data-id'))")
    # React Flow only renders the nodes inside the visible area, so this only asserts that part of the
    # pipeline is drawn and connected. The full ten-node check is in test_pipeline_structure.py.
    assert len(ids) >= 3, "expected at least 3 pipeline nodes in view, found " + str(ids)
    assert any(i.startswith("llm_node") or i.startswith("text_case_convert") for i in ids), ids
    expect(page.locator(".react-flow__edge").first).to_be_attached()
