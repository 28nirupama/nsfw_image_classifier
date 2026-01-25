import boto3
from botocore.client import Config as BotoConfig
from io import BytesIO
from config import config
import requests

# Lazy initialization of S3 client
_s3_client = None


def _get_s3_client():
    """Get or create S3 client. Returns None if S3 is disabled or not configured."""
    global _s3_client

    if not config.S3_UPLOAD_ENABLED:
        return None

    if _s3_client is None:
        # Debug: log AWS configuration
        print(f"DEBUG S3 Config - endpoint: {config.AWS_ENDPOINT_URL}")
        print(f"DEBUG S3 Config - access_key: {config.AWS_ACCESS_KEY_ID[:8] if config.AWS_ACCESS_KEY_ID else 'None'}...")
        print(f"DEBUG S3 Config - secret_key: {'***set***' if config.AWS_SECRET_ACCESS_KEY else 'None'}")
        print(f"DEBUG S3 Config - region: {config.AWS_REGION}")

        if not config.AWS_ACCESS_KEY_ID or not config.AWS_SECRET_ACCESS_KEY:
            print("Warning: AWS credentials not configured, S3 uploads disabled")
            return None

        _s3_client = boto3.client(
            's3',
            endpoint_url=config.AWS_ENDPOINT_URL,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version='s3v4'),
            region_name=config.AWS_REGION
        )

    return _s3_client


def upload_reported_image(image_buffer, filename, bucket):
    """Upload an image to the specified S3 bucket. Fails gracefully if S3 is not configured."""
    s3 = _get_s3_client()

    if s3 is None:
        print(f"S3 upload skipped (disabled or not configured): {filename}")
        return False

    try:
        print(f"Uploading image: {filename} to bucket: {bucket}")
        # Read content and create a fresh buffer to avoid corrupting the original
        image_buffer.seek(0)
        content = image_buffer.read()
        upload_buffer = BytesIO(content)
        s3.upload_fileobj(upload_buffer, bucket, filename)
        print(f"Image successfully uploaded to bucket: {bucket}")
        return True
    except Exception as e:
        print(f"Warning: S3 upload failed (non-fatal): {str(e)}")
        return False


def get_prediction_from_api(image_data):
    api_url = config.PREDICTION_API_URL
    response = requests.post(api_url, data=image_data, timeout=config.REQUEST_TIMEOUT)
    return response.json()

# Bucket name constants from config
ALL_IMAGES_BUCKET = config.S3_BUCKET_ALL_IMAGES
REPORTED_IMAGES_BUCKET = config.S3_BUCKET_NSFW_REPORTED
SAFE_REPORTED_BUCKET = config.S3_BUCKET_SAFE_REPORTED
