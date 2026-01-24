import boto3
from botocore.client import Config

s3 = boto3.client(
 's3',
 endpoint_url='https://storage.todos.monster',
 aws_access_key_id='JwmIA1pVSnTokCjetL3K',
 aws_secret_access_key='0bcVozMu1Ca84mlB9GdwX6YErIqALPD5ZxtWUgTH',
 config=Config(signature_version='s3v4'),
 region_name='us-east-1'
)

ALL_IMAGES_BUCKET = 'allimages'
REPORTED_IMAGES_BUCKET = 'nsfwreported'
