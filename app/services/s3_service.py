import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

BUCKET = settings.S3_BUCKET_NAME


async def upload_file_to_s3(file_bytes: bytes, filename: str, content_type: str) -> str:
    unique_filename = f"barbers/{uuid.uuid4()}_{filename}"

    try:
        s3_client.put_object(
            Bucket=BUCKET,
            Key=unique_filename,
            Body=file_bytes,
            ContentType=content_type,
            ACL="public-read",
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to S3: {str(e)}",
        )
    url = f"https://{BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
    return url


async def delete_file_from_s3(file_key: str):
    try:
        s3_client.delete_object(Bucket=BUCKET, Key=file_key)
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file from S3: {str(e)}",
        )
