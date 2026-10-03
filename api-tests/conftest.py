import pytest

from api_helpers import CREDITS, PROJECT_ID, TOKEN, Api


@pytest.fixture(scope="session")
def api():
    if not TOKEN:
        pytest.skip("RHOMBUS_TOKEN is not set in .env (see the README for how to get one)")
    client = Api(TOKEN)
    probe = client.get(CREDITS)
    if probe.status_code in (401, 403):
        pytest.fail(
            "RHOMBUS_TOKEN was rejected with HTTP " + str(probe.status_code)
            + ". It has probably expired. Copy a fresh one from the browser (see the README).",
            pytrace=False,
        )
    return client


@pytest.fixture(scope="session")
def project_id():
    if not PROJECT_ID:
        pytest.skip("RHOMBUS_PROJECT_ID is not set in .env")
    return PROJECT_ID
