import os
import re

import pytest
import requests
from playwright.sync_api import expect

from ui_helpers import go_to_executions_tab, poll_until, read_execution_rows, read_summary

TOKEN = os.environ.get("RHOMBUS_TOKEN", "")
SCHEDULES_URL = "https://api.rhombusai.com/api/dataset/analyzer/v2/pipeline/schedules/all"


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


def test_summary_cards_add_up(overview_page):
    s = read_summary(overview_page)
    assert s["successes"] + s["failures"] == s["executions"], s
    assert abs(round(100 * s["successes"] / s["executions"]) - s["rate"]) <= 1, s


def test_table_total_matches_the_executions_card(overview_page):
    page = overview_page
    card_total = read_summary(page)["executions"]
    go_to_executions_tab(page)
    m = re.search(r"\b\d+-\d+ of (\d+)\b", page.locator("body").inner_text())
    assert m, "could not find the pagination text (for example '1-10 of 25')"
    assert int(m.group(1)) == card_total, (
        "the table says " + m.group(1) + " executions but the Overview card says " + str(card_total))


def test_schedule_cards_match_the_backend(overview_page):
    if not TOKEN:
        pytest.skip("RHOMBUS_TOKEN is not set in .env")
    response = requests.get(SCHEDULES_URL, params={"page": 1, "page_size": 5},
                            headers={"Authorization": "Bearer " + TOKEN}, timeout=20)
    assert response.status_code == 200
    stats = response.json()["stats"]

    def cards_match():
        s = read_summary(overview_page)
        ok = s["schedules"] == stats["total_count"] and s["enabled"] == stats["enabled_count"]
        return s if ok else None
    poll_until(cards_match, timeout_s=20, interval_s=1,
               what="the schedule cards to show " + str(stats["total_count"]) + " schedule(s), "
                    + str(stats["enabled_count"]) + " enabled")


@pytest.mark.xfail(reason="Known issue: scheduled runs never fire, so no execution has a trigger other than "
                          "Manual (see observations/schedule-not-triggering.md)", strict=False)
def test_at_least_one_execution_was_triggered_by_the_schedule(dashboard_page):
    rows = read_execution_rows(dashboard_page)
    assert any(r["trigger"].lower() != "manual" for r in rows), "every execution on this page is Manual"
