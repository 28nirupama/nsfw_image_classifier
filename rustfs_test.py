import boto3
from botocore.client import Config
import os

# Set up your s3 client using boto3
s3 = boto3.client(
    's3',
    endpoint_url='https://storage.todos.monster',
    aws_access_key_id='JwmIA1pVSnTokCjetL3K',
    aws_secret_access_key='0bcVozMu1Ca84mlB9GdwX6YErIqALPD5ZxtWUgTH',
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
