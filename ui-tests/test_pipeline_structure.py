from playwright.sync_api import expect

CHAIN = ["input_node_1", "llm_node_1", "text_case_convert_node_1", "llm_node_2", "llm_node_3",
         "llm_node_4", "llm_node_5", "llm_node_6", "remove_duplicate_node_1"]
LABELS = {"input_node_1": "Data Input", "text_case_convert_node_1": "Text Case",
          "remove_duplicate_node_1": "Remove Duplicates"}


def node_ids(page):
    nodes = page.locator(".react-flow__node")
    expect(nodes).to_have_count(10, timeout=30000)
    return nodes.evaluate_all("els => els.map(e => e.getAttribute('data-id'))")


def output_node_id(ids):
    others = [i for i in ids if i not in CHAIN]
    assert len(others) == 1, "expected exactly one output node besides the chain, found " + str(others)
    return others[0]


def test_pipeline_has_ten_nodes_with_the_expected_ids(wide_project_page):
    ids = node_ids(wide_project_page)
    assert set(CHAIN).issubset(ids), "missing nodes: " + str(set(CHAIN) - set(ids))
    out_id = output_node_id(ids)
    expect(wide_project_page.locator('.react-flow__node[data-id="' + out_id + '"]')).to_contain_text("Data Output")


def test_nodes_carry_the_expected_labels(wide_project_page):
    node_ids(wide_project_page)
    for node_id, label in LABELS.items():
        expect(wide_project_page.locator('.react-flow__node[data-id="' + node_id + '"]')).to_contain_text(label)


def test_nodes_are_connected_in_order_from_input_to_output(wide_project_page):
    page = wide_project_page
    ids = node_ids(page)
    order = CHAIN + [output_node_id(ids)]
    for source, target in zip(order, order[1:]):
        edge = page.locator('[aria-label="Edge from ' + source + ' to ' + target + '"]')
        expect(edge, source + " should connect to " + target).to_be_attached()
