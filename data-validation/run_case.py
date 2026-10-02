import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

S3_BUCKET = os.environ["S3_BUCKET"]
S3_KEY = os.environ.get("S3_KEY", "input/baseline.csv")
GCS_BUCKET = os.environ["GCS_BUCKET"]
PREFIX = "RhombusAI_output_"
WAIT_MINUTES = 15
POLL_SECONDS = 10

BASELINE = Path("datasets/baseline.csv")
OUT_DIR = Path("datasets/outputs")
LOG_FILE = Path("datasets/run_records.jsonl")


def new_outputs(gcs, since):
    blobs = [b for b in gcs.list_blobs(GCS_BUCKET, prefix=PREFIX) if b.time_created > since]
    return sorted(blobs, key=lambda b: b.time_created)


def main():
    if len(sys.argv) != 3:
        print("usage: python data-validation/run_case.py <case_name> <dataset.csv>")
        sys.exit(1)

    case = sys.argv[1]
    dataset = Path(sys.argv[2])
    if not dataset.exists():
        print("dataset not found:", dataset)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    s3 = boto3.client("s3")
    gcs = storage.Client()

    record = {"case": case, "dataset": str(dataset), "status": "no_output", "outputs": []}

    try:
        s3.upload_file(str(dataset), S3_BUCKET, S3_KEY)
        uploaded_at = datetime.now(timezone.utc)
        record["uploaded_at"] = uploaded_at.isoformat()
        print("uploaded", dataset, "to s3://" + S3_BUCKET + "/" + S3_KEY)
        print("NOW press Run in Rhombus. Waiting up to", WAIT_MINUTES, "minutes for a new output...")

        deadline = time.time() + WAIT_MINUTES * 60
        found = []
        while time.time() < deadline:
            found = new_outputs(gcs, uploaded_at)
            if found:
                break
            time.sleep(POLL_SECONDS)

        if found:
            # Give any extra duplicate outputs a moment to show up
            time.sleep(20)
            found = new_outputs(gcs, uploaded_at)
            record["status"] = "output_found"
            for n, blob in enumerate(found):
                name = case + ".csv" if n == 0 else case + "__extra" + str(n + 1) + ".csv"
                blob.download_to_filename(str(OUT_DIR / name))
                record["outputs"].append({
                    "blob": blob.name,
                    "created": blob.time_created.isoformat(),
                    "saved_as": name,
                    "seconds_after_upload": round((blob.time_created - uploaded_at).total_seconds(), 1),
                })
            print("found", len(found), "output file(s); saved to", OUT_DIR)
            if len(found) > 1:
                print("NOTE: more than one output file appeared for one run. Write this down.")
        else:
            print("No output after", WAIT_MINUTES, "minutes.")
            print("Check Rhombus (Executions and Logs) for a failure and screenshot it.")
    finally:
        s3.upload_file(str(BASELINE), S3_BUCKET, S3_KEY)
        print("restored baseline.csv in S3")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    main()