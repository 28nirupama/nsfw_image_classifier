from config import Config
import boto3
from botocore.client import Config as BotoConfig
import os

# Load configuration
config = Config()

# Set up your s3 client using boto3 with environment variables
s3 = boto3.client(
    's3',
    endpoint_url=config.AWS_ENDPOINT_URL,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    config=BotoConfig(signature_version='s3v4'),
    region_name='us-east-1'
)

def upload_reported_image(image_buffer, filename, bucket):
    try:
        print(f"Uploading image: {filename} to bucket: {bucket}")  # Log upload attempt
        s3.upload_fileobj(image_buffer, bucket, filename)
        print(f"Image successfully uploaded to bucket: {bucket}")  # Log success
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        raise Exception(f"Error uploading image: {str(e)}")
