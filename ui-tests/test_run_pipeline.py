import os
import subprocess
import sys
from pathlib import Path

import boto3
import pytest
from google.cloud import storage
from playwright.sync_api import expect

from ui_helpers import dismiss_ad_blocker_modal, open_dashboard, open_project, poll_until, read_execution_rows

ROOT = Path(__file__).resolve().parents[1]
S3_BUCKET = os.environ.get("S3_BUCKET", "")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")
PREFIX = "RhombusAI_output_"
OUTPUT = ROOT / "datasets" / "outputs" / "ui_run_test.csv"


def test_run_button_produces_a_valid_output_in_gcs(page):
    if not S3_BUCKET or not GCS_BUCKET:
        pytest.skip("S3_BUCKET and GCS_BUCKET must be set in .env")
    s3, gcs = boto3.client("s3"), storage.Client()

    # Precondition: the source must hold the baseline, otherwise this test would be measuring a drift case.
    in_s3 = s3.get_object(Bucket=S3_BUCKET, Key="input/baseline.csv")["Body"].read()
    assert in_s3 == (ROOT / "datasets" / "baseline.csv").read_bytes(), (
        "S3 does not hold the baseline. Run: python -W ignore data-validation/swap_s3.py datasets/baseline.csv")

    dismiss_ad_blocker_modal(page)
    open_dashboard(page)
    before_number = max(r["number"] for r in read_execution_rows(page))
    before_files = {b.name for b in gcs.list_blobs(GCS_BUCKET, prefix=PREFIX)}

    open_project(page)
    run_button = page.locator("button:has(svg.lucide-play)")
    expect(run_button).to_have_count(1)
    run_button.click()

    def new_output():
        names = [b for b in gcs.list_blobs(GCS_BUCKET, prefix=PREFIX) if b.name not in before_files]
        return names[0] if names else None
    blob = poll_until(new_output, timeout_s=120, interval_s=3, what="a new output file in GCS")

    def newer_execution():
        open_dashboard(page)
        newest = max(read_execution_rows(page), key=lambda r: r["number"])
        return newest if newest["number"] > before_number else None
    newest = poll_until(newer_execution, timeout_s=90, interval_s=4, what="a new execution on the dashboard")
    assert newest["status"] == "Success", newest
    assert newest["trigger"] == "Manual", newest
    assert newest["nodes"] == "10 nodes", newest

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(str(OUTPUT))
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "data-validation/validate.py", "ui_run_test", str(OUTPUT),
         "--input", "datasets/baseline.csv"],
        cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, "validator reported failures:\n" + result.stdout[-1800:]
