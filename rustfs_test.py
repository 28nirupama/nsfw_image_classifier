import boto3
from botocore.client import Config as BotoConfig
from config import config

# Validate AWS credentials are set
config.validate()

# Set up S3 client using environment variables
s3 = boto3.client(
    's3',
    endpoint_url=config.AWS_ENDPOINT_URL,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    config=BotoConfig(signature_version='s3v4'),
    region_name=config.AWS_REGION
)


def upload_reported_image(image_buffer, filename, bucket):
    """Upload an image to the specified S3 bucket."""
    try:
        print(f"Uploading image: {filename} to bucket: {bucket}")
        image_buffer.seek(0)  # Ensure buffer is at the start
        s3.upload_fileobj(image_buffer, bucket, filename)
        print(f"Image successfully uploaded to bucket: {bucket}")
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        raise


# Bucket name constants from config
ALL_IMAGES_BUCKET = config.S3_BUCKET_ALL_IMAGES
REPORTED_IMAGES_BUCKET = config.S3_BUCKET_NSFW_REPORTED
SAFE_REPORTED_BUCKET = config.S3_BUCKET_SAFE_REPORTED
