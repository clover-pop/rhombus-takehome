import os
import re

import boto3
import pytest
from playwright.sync_api import expect

from ui_helpers import wait_for_full_pipeline

S3_BUCKET = os.environ.get("S3_BUCKET", "")
S3_TILE = re.compile(r"^\s*Amazon S3\s*$")
PROVIDERS = ("Amazon S3", "Azure Blob Storage", "Google Cloud Storage", "Snowflake")


def select_node(page, node):
    wait_for_full_pipeline(page)
    expect(node).to_have_count(1)
    node.click()
    return page.get_by_test_id("right-sidebar")


def sources_dialog(page):
    return page.get_by_role("dialog").filter(has_text="Third Party Data")


def open_sources_list(page):
    sidebar = select_node(page, page.locator('.react-flow__node[data-id="input_node_1"]'))
    sidebar.get_by_text("Third Party Sources").click()
    dialog = sources_dialog(page)
    # the list is ready once the connected source shows its Browse files button
    expect(dialog.get_by_role("button", name="Browse files").first).to_be_visible(timeout=30000)
    return dialog


def open_provider_list(page):
    dialog = open_sources_list(page)
    dialog.get_by_role("button", name="Add Data Sources").click()
    expect(dialog).to_contain_text("Select Data Source Provider")
    return dialog


def open_s3_form(page):
    dialog = open_provider_list(page)
    dialog.get_by_text(S3_TILE).last.click()
    bucket = dialog.locator('input[name="bucket"]')
    # the form first shows "Checking the managed-compute environment..." for a few seconds
    expect(bucket).to_be_visible(timeout=30000)
    return dialog, bucket


def test_source_provider_list_offers_four_providers(wide_project_page):
    dialog = open_provider_list(wide_project_page)
    for provider in PROVIDERS:
        expect(dialog).to_contain_text(provider)
    dialog.get_by_role("button", name="Cancel").click()
    expect(dialog).to_be_hidden()


def test_s3_form_shows_the_required_fields(wide_project_page):
    dialog, bucket = open_s3_form(wide_project_page)
    expect(bucket).to_have_attribute("placeholder", "company-analytics")
    expect(dialog).to_contain_text("Connection details")
    expect(dialog).to_contain_text("Bucket")
    expect(dialog).to_contain_text("Region")
    expect(dialog).to_contain_text("Asia Pacific (Sydney) (ap-southeast-2)")
    for label in ("Connect S3 source", "Back to Data Sources", "Cancel"):
        expect(dialog.get_by_role("button", name=label)).to_be_visible()


def test_s3_form_with_an_empty_bucket_creates_nothing(wide_project_page):
    page = wide_project_page
    dialog = open_sources_list(page)
    sources_before = dialog.get_by_text("Amazon S3").count()
    assert sources_before >= 1, "the connected S3 source should be listed"

    dialog.get_by_role("button", name="Add Data Sources").click()
    dialog.get_by_text(S3_TILE).last.click()
    bucket = dialog.locator('input[name="bucket"]')
    expect(bucket).to_be_visible(timeout=30000)
    expect(bucket).to_have_value("")

    connect = dialog.get_by_role("button", name="Connect S3 source")
    if connect.is_enabled():
        connect.click()
        # the form must not move on to a connected state
        expect(bucket).to_be_visible()
        expect(bucket).to_have_value("")

    dialog.get_by_role("button", name="Cancel").click()
    expect(dialog).to_be_hidden()

    page.get_by_test_id("right-sidebar").get_by_text("Third Party Sources").click()
    dialog = sources_dialog(page)
    expect(dialog.get_by_role("button", name="Browse files").first).to_be_visible(timeout=30000)
    assert dialog.get_by_text("Amazon S3").count() == sources_before, "a new source appeared in the list"
    expect(dialog.get_by_role("button", name="Browse files")).to_have_count(1)


def test_browse_files_shows_the_baseline_with_the_size_stored_in_s3(wide_project_page):
    if not S3_BUCKET:
        pytest.skip("S3_BUCKET is not set in .env")
    dialog = open_sources_list(wide_project_page)
    dialog.get_by_role("button", name="Browse files").first.click()
    expect(dialog).to_contain_text("input/baseline.csv", timeout=30000)
    expect(dialog).to_contain_text("s3://" + S3_BUCKET + "/input/")
    expect(dialog).to_contain_text("supported file")
    expect(dialog).to_contain_text("ap-southeast-2")

    text = re.sub(r"\s+", " ", dialog.inner_text())
    match = re.search(r"input/baseline\.csv\s*([\d.]+)\s*KB", text)
    assert match, "no size is shown for baseline.csv: " + text[:300]
    shown_kb = float(match.group(1))
    size = boto3.client("s3").head_object(Bucket=S3_BUCKET, Key="input/baseline.csv")["ContentLength"]
    # the screen rounds to one decimal and may use 1000 or 1024 bytes per KB
    assert min(abs(shown_kb - size / 1024), abs(shown_kb - size / 1000)) <= 0.06, (
        "the screen shows " + str(shown_kb) + " KB but S3 holds " + str(size) + " bytes")


def test_gcs_destination_form_cannot_be_created_without_credentials(wide_project_page):
    page = wide_project_page
    sidebar = select_node(page, page.locator(".react-flow__node", has_text="Data Output"))
    sidebar.get_by_text("Add New Destination").first.click()

    chooser = page.get_by_role("dialog").filter(has_text="Select Destination Provider")
    expect(chooser).to_be_visible()
    for provider in PROVIDERS + ():
        expect(chooser).to_contain_text(provider)
    chooser.get_by_text("Google Cloud Storage", exact=True).click()

    form = page.get_by_role("dialog").filter(has_text="Configure your Google Cloud Storage destination")
    expect(form).to_be_visible()
    for permission in ("storage.buckets.get", "storage.objects.create",
                       "storage.objects.get", "storage.objects.list"):
        expect(form).to_contain_text(permission)

    create = form.get_by_role("button", name="Create Destination")
    expect(create).to_be_disabled()
    form.locator('input[name="bucket"]').fill("not-a-real-bucket-name")
    expect(create).to_be_disabled()  # still needs the service account JSON


def test_add_transformation_menu_lists_the_building_blocks(project_page):
    page = project_page
    page.locator('button:has(svg[class*="lucide-plus"][class*="h-[18px]"])').first.click()
    menu = (page.locator("[role=dialog], [role=menu], [data-radix-popper-content-wrapper]")
            .filter(has_text="Add Transformation").first)
    expect(menu).to_be_visible()
    for text in ("Data Input", "Data Output", "Organize", "Combine & Shape",
                 "Transform & Enhance", "Clean & Format", "Detect & Manage"):
        expect(menu).to_contain_text(text)
