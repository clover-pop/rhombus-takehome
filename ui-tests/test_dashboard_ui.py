import os
import re

import pytest
import requests
from playwright.sync_api import expect

from ui_helpers import read_execution_rows

TOKEN = os.environ.get("RHOMBUS_TOKEN", "")
SCHEDULES_URL = "https://api.rhombusai.com/api/dataset/analyzer/v2/pipeline/schedules/all"
SUMMARY_RE = re.compile(
    r"Executions\s+(\d+)\s+Recent runs\s+Success rate\s+(\d+)%\s+(\d+) successful\s+Failures\s+(\d+)"
    r"\s+Need attention\s+Schedules\s+(\d+)\s+(\d+) enabled"
)


def read_summary(page):
    expect(page.locator("body")).to_contain_text(re.compile(r"Executions\s+[1-9]\d*\s+Recent runs"), timeout=30000)
    m = SUMMARY_RE.search(page.locator("body").inner_text())
    assert m, "could not find the summary cards in the page text"
    keys = ["executions", "rate", "successes", "failures", "schedules", "enabled"]
    return dict(zip(keys, (int(x) for x in m.groups())))


def test_executions_table_has_the_expected_columns(dashboard_page):
    header = dashboard_page.locator("thead").first
    expect(header).to_contain_text(re.compile(
        r"Execution.*Trigger.*Project.*Started.*Duration.*Status.*Nodes", re.S))


def test_every_execution_row_is_well_formed_and_newest_first(dashboard_page):
    rows = read_execution_rows(dashboard_page)
    assert rows, "the table has no rows"
    numbers = [r["number"] for r in rows]
    assert numbers == sorted(numbers, reverse=True), "rows should be newest first: " + str(numbers)
    assert len(set(numbers)) == len(numbers), "execution numbers should be unique"
    for r in rows:
        assert r["project"] == "rhombus-takehome"
        assert r["duration_s"] >= 0


def test_summary_cards_add_up(dashboard_page):
    s = read_summary(dashboard_page)
    assert s["successes"] + s["failures"] == s["executions"], s
    assert abs(round(100 * s["successes"] / s["executions"]) - s["rate"]) <= 1, s


def test_table_total_matches_the_executions_card(dashboard_page):
    s = read_summary(dashboard_page)
    text = dashboard_page.locator("body").inner_text()
    m = re.search(r"\d+-\d+ of (\d+)", text)
    assert m, "could not find the pagination text"
    assert int(m.group(1)) == s["executions"], "table says " + m.group(1) + " but the card says " + str(s["executions"])


def test_schedule_cards_match_the_backend(dashboard_page):
    if not TOKEN:
        pytest.skip("RHOMBUS_TOKEN is not set in .env")
    s = read_summary(dashboard_page)
    response = requests.get(SCHEDULES_URL, params={"page": 1, "page_size": 5},
                            headers={"Authorization": "Bearer " + TOKEN}, timeout=20)
    assert response.status_code == 200
    stats = response.json()["stats"]
    assert s["schedules"] == stats["total_count"]
    assert s["enabled"] == stats["enabled_count"]


@pytest.mark.xfail(reason="Known issue: scheduled runs never fire, so no execution has a trigger other than Manual "
                          "(see observations/schedule-not-triggering.md)", strict=False)
def test_at_least_one_execution_was_triggered_by_the_schedule(dashboard_page):
    rows = read_execution_rows(dashboard_page)
    assert any(r["trigger"].lower() != "manual" for r in rows), "every execution on this page is Manual"
