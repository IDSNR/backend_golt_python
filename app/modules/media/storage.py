from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from urllib.parse import quote


@dataclass(frozen=True)
class StoredMedia:
    key: str
    url: str


class MediaStorage(Protocol):
    def store(self, file_object: BinaryIO, key: str, content_type: str) -> StoredMedia: ...


class LocalMediaStorage:
    def __init__(self, folder: str, url_path: str) -> None:
        self.folder = Path(folder)
        self.url_path = url_path.rstrip("/")
        self.folder.mkdir(parents=True, exist_ok=True)

    def store(self, file_object: BinaryIO, key: str, content_type: str) -> StoredMedia:
        destination = self.folder / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f"{destination.name}.uploading")
        try:
            with temporary.open("wb") as output:
                while chunk := file_object.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return StoredMedia(key=key, url=f"{self.url_path}/{quote(key, safe='/')}")


class S3MediaStorage:
    def __init__(
        self,
        *,
        bucket: str,
        cdn_base_url: str,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        client=None,
    ) -> None:
        if not bucket or not cdn_base_url:
            raise ValueError("OBJECT_STORAGE_BUCKET and MEDIA_CDN_BASE_URL are required for S3 storage")

        self.bucket = bucket
        self.cdn_base_url = cdn_base_url.rstrip("/")
        if client is None:
            import boto3

            client = boto3.client(
                "s3",
                region_name=region,
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
            )
        self.client = client

    def store(self, file_object: BinaryIO, key: str, content_type: str) -> StoredMedia:
        self.client.upload_fileobj(
            file_object,
            self.bucket,
            key,
            ExtraArgs={
                "ContentType": content_type,
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )
        return StoredMedia(key=key, url=f"{self.cdn_base_url}/{quote(key, safe='/')}")


def build_media_storage(settings) -> MediaStorage:
    if settings.media_storage_backend == "local":
        return LocalMediaStorage(settings.media_folder, settings.media_url_path)
    return S3MediaStorage(
        bucket=settings.object_storage_bucket or "",
        cdn_base_url=settings.media_cdn_base_url or "",
        region=settings.object_storage_region,
        endpoint_url=settings.object_storage_endpoint_url,
        access_key_id=settings.object_storage_access_key_id,
        secret_access_key=settings.object_storage_secret_access_key,
    )
