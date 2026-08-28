import os
import sys
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configuration
BUCKET_NAME = "bug-trage-proj-s333"  # Replace with your actual S3 bucket name
S3_PREFIX = "v1"
ARTIFACTS_DIR = "ml_artifacts"

CLASSIFIER_FILE = "classifier.onnx"
EMBEDDINGS_FILE = "embeddings.onnx"

def download_from_s3(s3_client, bucket: str, s3_key: str, local_path: str):
    print(f"📥 [S3 FETCH] Downloading s3://{bucket}/{s3_key} -> {local_path}...")
    try:
        s3_client.download_file(bucket, s3_key, local_path)
        print(f"✅ [S3 FETCH] Successfully downloaded {local_path}")
    except (BotoCoreError, ClientError) as e:
        print(f"❌ [S3 FETCH ERROR] Failed to download {s3_key} from S3: {e}")
        sys.exit(1)

def fetch_model_artifacts():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    local_classifier = os.path.join(ARTIFACTS_DIR, CLASSIFIER_FILE)
    local_embeddings = os.path.join(ARTIFACTS_DIR, EMBEDDINGS_FILE)

    # Initialize Boto3 S3 Client
    s3_client = boto3.client("s3")

    # Fetch Classifier ONNX model
    if not os.path.exists(local_classifier):
        download_from_s3(s3_client, BUCKET_NAME, f"{S3_PREFIX}/{CLASSIFIER_FILE}", local_classifier)
    else:
        print(f"✅ [CACHE] {local_classifier} already exists.")

    # Fetch Embeddings ONNX model
    if not os.path.exists(local_embeddings):
        download_from_s3(s3_client, BUCKET_NAME, f"{S3_PREFIX}/{EMBEDDINGS_FILE}", local_embeddings)
    else:
        print(f"✅ [CACHE] {local_embeddings} already exists.")

if __name__ == "__main__":
    fetch_model_artifacts()