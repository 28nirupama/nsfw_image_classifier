import boto3
from botocore.client import Config
import os

# Initialize the S3 client
s3 = boto3.client(
 's3',
 endpoint_url='https://storage.todos.monster',
 aws_access_key_id='JwmIA1pVSnTokCjetL3K',
 aws_secret_access_key='0bcVozMu1Ca84mlB9GdwX6YErIqALPD5ZxtWUgTH',
 config=Config(signature_version='s3v4'),
 region_name='us-east-1'
)

# Bucket names
ALL_IMAGES_BUCKET = 'allimages'
REPORTED_IMAGES_BUCKET = 'nsfwreported'


def upload_image_to_bucket(file_path, bucket_name, s3_object_name):
    """
    Uploads an image to the specified bucket.
    :param file_path: Path to the local file to be uploaded
    :param bucket_name: Name of the bucket to upload to
    :param s3_object_name: The object name in S3 (can be same as file name)
    """
    try:
        s3.upload_file(file_path, bucket_name, s3_object_name)
        print(f"File {file_path} uploaded to {bucket_name} as {s3_object_name}")
    except Exception as e:
        print(f"Error uploading {file_path} to {bucket_name}: {e}")


def upload_uploaded_image(file, s3_object_name):
    """
    Upload an uploaded image to `allimages` bucket.
    :param file: The file object to be uploaded
    :param s3_object_name: The object name in S3
    """
    file_path = os.path.join("temp_images", s3_object_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    file.save(file_path)  # Save the uploaded file temporarily

    # Upload the file to `allimages`
    upload_image_to_bucket(file_path, ALL_IMAGES_BUCKET, s3_object_name)


def upload_reported_image(image, s3_object_name):
    """
    Upload a reported image to `nsfwreported` bucket.
    :param image: PIL image object to be uploaded
    :param s3_object_name: The object name in S3
    """
    file_path = os.path.join("reported_images", s3_object_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    image.save(file_path)  # Save the image temporarily

    # Upload the file to `nsfwreported`
    upload_image_to_bucket(file_path, REPORTED_IMAGES_BUCKET, s3_object_name)
