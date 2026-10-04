import pytest

from ui_helpers import STATE, dismiss_ad_blocker_modal, open_dashboard, open_project


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    if not STATE.exists():
        pytest.skip("secrets/auth_state.json is missing (see the README: run ui-tests/save_login_cdp.py)")
    return {**browser_context_args, "storage_state": str(STATE), "viewport": {"width": 1600, "height": 900}}


@pytest.fixture
def project_page(page):
    dismiss_ad_blocker_modal(page)
    open_project(page)
    return page


@pytest.fixture
def wide_project_page(page):
    page.set_viewport_size({"width": 3400, "height": 1000})
    dismiss_ad_blocker_modal(page)
    open_project(page)
    return page


@pytest.fixture
def dashboard_page(page):
    dismiss_ad_blocker_modal(page)
    open_dashboard(page, "Executions")
    return page


@pytest.fixture
def overview_page(page):
    dismiss_ad_blocker_modal(page)
    open_dashboard(page, "Overview")
    return page
