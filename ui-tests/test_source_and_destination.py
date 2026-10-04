import os

import boto3
import pytest
from google.cloud import storage
from playwright.sync_api import expect

from ui_helpers import wait_for_full_pipeline

S3_BUCKET = os.environ.get("S3_BUCKET", "")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")


def click_node(page, node):
    wait_for_full_pipeline(page)
    expect(node).to_have_count(1)
    node.click()
    return page.get_by_test_id("right-sidebar")


def input_node(page):
    return page.locator('.react-flow__node[data-id="input_node_1"]')


def output_node(page):
    return page.locator(".react-flow__node", has_text="Data Output")


def test_data_input_panel_shows_the_dataset_and_upload_options(wide_project_page):
    sidebar = click_node(wide_project_page, input_node(wide_project_page))
    expect(sidebar).to_contain_text("Select Dataset")
    expect(sidebar).to_contain_text("baseline.csv")
    for option in ("From Device", "From Web URL", "Third Party Sources"):
        expect(sidebar).to_contain_text(option)
    expect(sidebar).to_contain_text("Enable Sampling")


def test_s3_source_is_connected_and_points_at_my_bucket(wide_project_page):
    if not S3_BUCKET:
        pytest.skip("S3_BUCKET is not set in .env")
    page = wide_project_page
    sidebar = click_node(page, input_node(page))
    sidebar.get_by_text("Third Party Sources").click()

    expect(page.get_by_text("Third Party Data").first).to_be_visible()
    for text in ("baseline-s3-source", "Amazon S3", "Connected",
                 "s3://" + S3_BUCKET + "/input/", "ap-southeast-2"):
        expect(page.get_by_text(text).first, text + " should be shown").to_be_visible()

    # Real outcome: the file the pipeline reads is really there.
    head = boto3.client("s3").head_object(Bucket=S3_BUCKET, Key="input/baseline.csv")
    assert head["ContentLength"] > 0

    page.get_by_role("button", name="Cancel").first.click()
    expect(page.get_by_text("Third Party Data").first).to_be_hidden()


def test_data_output_panel_points_at_my_gcs_bucket(wide_project_page):
    if not GCS_BUCKET:
        pytest.skip("GCS_BUCKET is not set in .env")
    page = wide_project_page
    sidebar = click_node(page, output_node(page))
    expect(sidebar).to_contain_text("Select Destination")
    expect(sidebar).to_contain_text(GCS_BUCKET)
    expect(sidebar).to_contain_text("Export Configuration")
    expect(sidebar).to_contain_text("Export Format")
    expect(sidebar).to_contain_text("CSV")
    expect(sidebar).to_contain_text("Data will be exported automatically when the pipeline runs.")

    # Real outcome: the bucket exists and my service account can list it.
    list(storage.Client().list_blobs(GCS_BUCKET, max_results=1))
