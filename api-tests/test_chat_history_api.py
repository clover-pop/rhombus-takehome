import pytest

from api_helpers import HISTORY, json_body, parse_ts


def path_for(project_id):
    return HISTORY.format(project_id=project_id)


@pytest.fixture(scope="module")
def history(api, project_id):
    return json_body(api.get(path_for(project_id), params={"limit": 50, "structured": "true"}))


def test_history_envelope_is_consistent(history):
    messages = history["history"]
    assert isinstance(messages, list)
    assert len(messages) <= 50
    assert history["count"] == len(messages)
    assert history.get("structured") is True
    assert "next_before" in history


def test_every_message_is_well_formed(history):
    messages = history["history"]
    assert len({m["id"] for m in messages}) == len(messages), "message ids should be unique"
    for m in messages:
        assert isinstance(m["id"], int)
        assert m["role"] in ("user", "assistant")
        parse_ts(m["created_at"])
        assert isinstance(m["thread_id"], str) and m["thread_id"]
        assert isinstance(m["run_id"], str) and m["run_id"]
        assert isinstance(m["content"], dict)
        if m["role"] == "user":
            assert isinstance(m["content"]["message"], str)
        else:
            assert isinstance(m["content"]["status"], str)


def test_every_reply_has_a_user_message_in_the_same_run(history):
    messages = history["history"]
    if len(messages) >= 50:
        pytest.skip("history is truncated, runs may be cut in half")
    user_runs = {m["run_id"] for m in messages if m["role"] == "user"}
    for m in messages:
        if m["role"] == "assistant":
            assert m["run_id"] in user_runs, "assistant message " + str(m["id"]) + " has no matching question"


def test_limit_parameter_is_respected(api, project_id):
    body = json_body(api.get(path_for(project_id), params={"limit": 1, "structured": "true"}))
    assert len(body["history"]) <= 1
