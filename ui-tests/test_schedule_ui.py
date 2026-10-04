import os
import re

import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import expect

load_dotenv()
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "5009")
TOKEN = os.environ.get("RHOMBUS_TOKEN", "")
SCHEDULES_URL = "https://api.rhombusai.com/api/dataset/analyzer/v2/pipeline/schedules/all"


def backend_list():
    if not TOKEN:
        pytest.skip("RHOMBUS_TOKEN is not set in .env")
    response = requests.get(SCHEDULES_URL, params={"page": 1, "page_size": 5},
                            headers={"Authorization": "Bearer " + TOKEN}, timeout=20)
    assert response.status_code == 200, "schedules API returned " + str(response.status_code)
    return response.json()


def backend_schedule():
    mine = [s for s in backend_list()["schedules"] if str(s["project_id"]) == PROJECT_ID]
    assert mine, "the backend lists no schedule for project " + PROJECT_ID
    return mine[0]


def open_schedule_tab(page):
    page.get_by_role("tab", name="Schedule").click()
    sidebar = page.get_by_test_id("right-sidebar")
    expect(sidebar).to_contain_text("Schedules")
    return sidebar


def schedule_card(page):
    # The right sidebar also contains the AI Builder chat, so every assertion is scoped to the card:
    # the smallest div that holds the schedule title, the "Next run" line and the on/off switch.
    sidebar = page.get_by_test_id("right-sidebar")
    switch = page.get_by_role("switch", name=re.compile("activate schedule", re.I))
    card = (sidebar.locator("div")
            .filter(has_text=re.compile(r"Schedule for rhombus-takehome.*Next run", re.S))
            .filter(has=switch)
            .last)
    expect(card).to_be_visible()
    return card


def test_schedule_tab_shows_an_active_schedule(project_page):
    open_schedule_tab(project_page)
    card = schedule_card(project_page)
    expect(card).to_contain_text("Active")
    expect(card.get_by_role("switch", name="Deactivate schedule")).to_be_visible()
    expect(card.get_by_role("button", name="Notify on failure")).to_be_visible()


def test_ui_schedule_matches_the_backend(project_page):
    schedule = backend_schedule()
    open_schedule_tab(project_page)
    card = schedule_card(project_page)
    expect(card).to_contain_text(schedule["name"])
    if schedule["frequency"] == "hourly":
        minute = int(schedule["cron_expression"].split()[0])
        # The DOM holds "hourly" and CSS capitalises it, so match without case.
        expect(card).to_contain_text(re.compile("hourly", re.I))
        expect(card).to_contain_text("At minute " + str(minute))
    else:
        expect(card).to_contain_text(schedule["cron_expression"])
    if schedule["enabled"]:
        expect(card.get_by_role("switch", name="Deactivate schedule")).to_be_visible()


def test_add_schedule_dialog_can_be_cancelled_without_creating_anything(project_page):
    page = project_page
    total_before = backend_list()["total"]
    sidebar = open_schedule_tab(page)
    sidebar.get_by_role("button", name="Add Schedule").click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text("Create Schedule")
    expect(dialog).to_contain_text("Frequency")
    expect(dialog).to_contain_text("Notify on failure")
    dialog.get_by_role("button", name="Cancel").click()
    expect(dialog).to_be_hidden()
    assert backend_list()["total"] == total_before, "cancelling the dialog must not create a schedule"


@pytest.mark.xfail(reason="Known issue: the schedule card shows no next run time "
                          "(see observations/schedule-not-triggering.md)", strict=False)
def test_schedule_card_shows_a_next_run_time(project_page):
    open_schedule_tab(project_page)
    card = schedule_card(project_page)
    expect(card).to_contain_text(re.compile(r"Next run:\s*\S"), timeout=5000)
