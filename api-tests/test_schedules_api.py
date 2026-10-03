import re
from datetime import timedelta

import pytest

from api_helpers import SCHEDULES, json_body, parse_ts, utcnow

REQUIRED = ["id", "project_id", "name", "frequency", "schedule_time_utc", "cron_expression",
            "enabled", "notify_on_failure", "next_run_at", "last_run_at", "created_at",
            "skipped_runs_count"]

KNOWN_ISSUE = ("Known issue: scheduled runs never fire "
               "(see observations/schedule-not-triggering.md)")


@pytest.fixture(scope="module")
def listing(api):
    return json_body(api.get(SCHEDULES, params={"page": 1, "page_size": 5}))


@pytest.fixture(scope="module")
def schedules(listing):
    items = listing["schedules"]
    if not items:
        pytest.skip("no schedules in this account")
    return items


def test_list_totals_are_consistent(listing):
    items, stats = listing["schedules"], listing["stats"]
    assert listing["page"] == 1
    assert listing["page_size"] == 5
    assert len(items) <= listing["page_size"]
    assert listing["total"] == stats["total_count"]
    if listing["total"] <= listing["page_size"]:
        assert len(items) == listing["total"]
        assert stats["enabled_count"] == sum(1 for s in items if s["enabled"])
        assert sum(stats["frequency_counts"].values()) == listing["total"]


def test_every_schedule_has_the_expected_fields(schedules):
    for s in schedules:
        for key in REQUIRED:
            assert key in s, "schedule is missing " + key
        assert isinstance(s["id"], int)
        assert isinstance(s["project_id"], int)
        assert isinstance(s["enabled"], bool)
        assert isinstance(s["skipped_runs_count"], int) and s["skipped_runs_count"] >= 0
        parse_ts(s["created_at"])
        if s["next_run_at"] is not None:
            parse_ts(s["next_run_at"])
        if s["last_run_at"] is not None:
            parse_ts(s["last_run_at"])


def test_cron_expression_matches_the_frequency_label(schedules):
    for s in schedules:
        assert len(s["cron_expression"].split()) == 5, "cron should have five fields"
        if s["frequency"] == "hourly":
            match = re.fullmatch(r"(\d{1,2}) \* \* \* \*", s["cron_expression"])
            assert match, "hourly schedule should look like 'M * * * *': " + s["cron_expression"]
            minute = int(match.group(1))
            assert 0 <= minute <= 59
            assert s["schedule_time_utc"] == "*:" + "%02d" % minute


@pytest.mark.xfail(reason=KNOWN_ISSUE, strict=False)
def test_enabled_schedule_next_run_is_not_stale(schedules):
    now = utcnow()
    for s in schedules:
        if s["enabled"]:
            assert s["next_run_at"] is not None, "schedule " + str(s["id"]) + " has no next_run_at"
            assert parse_ts(s["next_run_at"]) > now - timedelta(minutes=10), (
                "schedule " + str(s["id"]) + " next_run_at " + s["next_run_at"] + " is in the past"
            )


@pytest.mark.xfail(reason=KNOWN_ISSUE, strict=False)
def test_enabled_hourly_schedule_has_run_at_least_once(schedules):
    now = utcnow()
    old_enough = [s for s in schedules
                  if s["enabled"] and s["frequency"] == "hourly"
                  and now - parse_ts(s["created_at"]) > timedelta(hours=2)]
    if not old_enough:
        pytest.skip("no enabled hourly schedule older than two hours")
    for s in old_enough:
        assert s["last_run_at"] is not None, (
            "schedule " + str(s["id"]) + " created " + s["created_at"] + " has never run"
        )
