import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()
s3 = boto3.client("s3")
body = s3.get_object(Bucket=os.environ["S3_BUCKET"], Key="input/baseline.csv")["Body"].read()
local = Path("datasets/baseline.csv").read_bytes()
print("S3 matches local baseline:", body == local)
