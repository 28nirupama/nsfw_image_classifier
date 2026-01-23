import boto3
from botocore.client import Config
import os

# Configure boto3 client for RustFS (local or remote)
s3 = boto3.client(
 's3',
 endpoint_url='https://storage.todos.monster',
 aws_access_key_id='JwmIA1pVSnTokCjetL3K',
 aws_secret_access_key='0bcVozMu1Ca84mlB9GdwX6YErIqALPD5ZxtWUgTH',
 config=Config(signature_version='s3v4'),
 region_name='us-east-1'
)

# Buckets for different image types
reported_images_bucket = 'nsfwreported'
uploaded_images_bucket = 'allimages'

def upload_file_to_s3(file_path, bucket_name, s3_object_name):
    """
    Upload a file to a specified S3 bucket.
    Args:
    - file_path: Local path to the file.
    - bucket_name: The name of the S3 bucket.
    - s3_object_name: The name to be used for the file in S3.
    """
    try:
        s3.upload_file(file_path, bucket_name, s3_object_name)
        print(f'File {file_path} uploaded to {bucket_name} as {s3_object_name}.')
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")

def upload_image_from_url(image_url, bucket_name, s3_object_name):
    """
    Download an image from a URL and upload it to S3.
    Args:
    - image_url: The URL of the image.
    - bucket_name: The S3 bucket name.
    - s3_object_name: The name to be used for the image in S3.
    """
    import requests
    
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(s3_object_name, 'wb') as f:
                f.write(response.content)
            # Upload the file to S3
            upload_file_to_s3(s3_object_name, bucket_name, s3_object_name)
            os.remove(s3_object_name)  # Delete the temporary file after upload
        else:
            print(f"Error: Unable to download image from {image_url}")
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")

# Example of uploading a local file to the 'reported' bucket
local_file = 'hello.txt'  # Update with your actual file
upload_file_to_s3(local_file, reported_images_bucket, 'hello.txt')

# Example of uploading a file from a URL to the 'uploaded' bucket
image_url = 'https://example.com/image.jpg'  # Replace with the actual image URL
upload_image_from_url(image_url, uploaded_images_bucket, 'image_from_url.jpg')
