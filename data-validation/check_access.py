import os

import boto3
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

s3 = boto3.client("s3")
r = s3.list_objects_v2(Bucket=os.environ["S3_BUCKET"], Prefix="input/")
print("S3 input/:", [o["Key"] for o in r.get("Contents", [])])

gcs = storage.Client()
print("GCS files:", len(list(gcs.list_blobs(os.environ["GCS_BUCKET"]))))
