import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()
boto3.client("s3").upload_file(sys.argv[1], os.environ["S3_BUCKET"], "input/baseline.csv")
print("uploaded", sys.argv[1], "as input/baseline.csv")
