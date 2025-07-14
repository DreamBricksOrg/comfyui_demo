import os
import uuid
import structlog

import boto3
from botocore.client import Config

from core.config import settings


log = structlog.get_logger()


# Usa o próprio boto3 para verificar se existe credenciais configuradas
def has_aws_credentials() -> bool:
    session = boto3.Session()
    return session.get_credentials() is not None

USE_S3 = has_aws_credentials()

if USE_S3:
    ENDPOINT = f"https://s3.{settings.AWS_REGION}.amazonaws.com"
    s3_client = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        region_name=settings.AWS_REGION,
        config=Config(signature_version="s3v4"),
    )
else:
    s3_client = None

def public_url(key: str) -> str:
    if USE_S3:
        return f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    return f"{settings.BASE_URL}/image/{key}"


def upload_fileobj(file_obj, key_prefix: str, extension: str = "png") -> str:
    """Upload de arquivo para S3 ou armazenamento local."""
    key = f"{key_prefix}/{uuid.uuid4()}.{extension}"
    log.debug(f"USE_S3: {USE_S3}")
    if USE_S3:
        s3_client.upload_fileobj(
            file_obj,
            settings.S3_BUCKET,
            key,
            ExtraArgs={"ContentType": f"image/{extension}"},
        )
    else:
        dest = os.path.join(settings.STATIC_DIR, key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        file_obj.seek(0)
        with open(dest, "wb") as f:
            f.write(file_obj.read())
        log.debug(f"[upload_fileobj] Saved image at {dest}")
    return key


def create_presigned_upload(key_prefix: str, content_type: str, expires_in: int = 3600):
    key = f"{key_prefix}/{uuid.uuid4()}"
    if USE_S3:
        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        return {"url": url, "key": key}
    else:
        return {"url": None, "key": key}


def create_presigned_download(key: str, expires_in: int = 3600) -> str:
    if USE_S3:
        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )
    return f"{settings.BASE_URL}/image/{key}"

def download_file(key: str) -> bytes:
    """Baixa arquivo do S3 ou do armazenamento local."""
    if USE_S3:
        obj = s3_client.get_object(Bucket=settings.S3_BUCKET, Key=key)
        return obj["Body"].read()
    path = os.path.join(settings.STATIC_DIR, key)
    with open(path, "rb") as f:
        return f.read()
