import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()
blobs = sorted(storage.Client().list_blobs(os.environ["GCS_BUCKET"]), key=lambda b: b.time_created, reverse=True)[:6]
for b in blobs:
    when = b.time_created.astimezone(ZoneInfo("Australia/Sydney")).strftime("%d %b %H:%M:%S")
    print(when, b.name[:40], b.size, "bytes")
