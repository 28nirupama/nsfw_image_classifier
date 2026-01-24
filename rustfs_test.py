from dotenv import load_dotenv
import os
import boto3
from botocore.client import Config

# Load environment variables from .env file
load_dotenv()

# Ensure the environment variables are loaded correctly
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
STORAGE_ENDPOINT_URL = os.getenv('STORAGE_ENDPOINT_URL')

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, STORAGE_ENDPOINT_URL]):
    raise EnvironmentError("Missing environment variables. Please check your .env file.")

# Set up your s3 client using boto3 with environment variables
s3 = boto3.client(
    's3',
    endpoint_url=STORAGE_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

def upload_reported_image(image_buffer, filename, bucket):
    try:
        print(f"Uploading image: {filename} to bucket: {bucket}")  # Log upload attempt
        # Ensure the buffer is open and passed correctly
        s3.upload_fileobj(image_buffer, bucket, filename)
        print(f"Image successfully uploaded to bucket: {bucket}")  # Log success
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        raise Exception(f"Error uploading image: {str(e)}")

# These can be useful for static bucket references
ALL_IMAGES_BUCKET = 'allimages'
REPORTED_IMAGES_BUCKET = 'nsfwreported'
SAFE_REPORTED_BUCKET = 'safereported'  # New bucket for safe reports
