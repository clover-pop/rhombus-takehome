import time

from api_helpers import CREDITS, PROFILE, json_body

INT_FIELDS = ["balance", "subscription_credits", "purchased_credits",
              "monthly_allocation", "usage_this_period"]


def test_credits_response_is_consistent(api):
    started = time.time()
    response = api.get(CREDITS)
    elapsed = time.time() - started
    body = json_body(response)
    assert elapsed < 10, "credits took " + str(round(elapsed, 1)) + " seconds"

    balance = body["balance"]
    for key in INT_FIELDS:
        value = balance[key]
        assert isinstance(value, int) and not isinstance(value, bool), key + " should be an integer"
        assert value >= 0, key + " should not be negative"
    assert balance["balance"] == balance["subscription_credits"] + balance["purchased_credits"]
    assert isinstance(balance["is_unlimited"], bool)
    assert isinstance(balance["topup_enabled"], bool)
    assert body["tier_info"]["tier"] == balance["tier"]
    assert body["tier_info"]["monthly_credits"] == balance["monthly_allocation"]
    assert isinstance(body["topup_packages"], list)


def test_profile_has_name_fields_and_leaks_nothing_sensitive(api):
    body = json_body(api.get(PROFILE))
    assert isinstance(body, dict)
    for key in ("first_name", "last_name"):
        assert key in body, "missing field " + key
        assert body[key] is None or isinstance(body[key], str)
    risky = [k for k in body if any(w in k.lower() for w in ("token", "password", "secret"))]
    assert not risky, "profile exposes sensitive-looking fields: " + str(risky)
