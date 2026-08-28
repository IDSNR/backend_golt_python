from io import BytesIO

from app.modules.media.storage import LocalMediaStorage, S3MediaStorage


class FakeS3Client:
    def __init__(self) -> None:
        self.upload = None

    def upload_fileobj(self, file_object, bucket, key, ExtraArgs):
        self.upload = {
            "body": file_object.read(),
            "bucket": bucket,
            "key": key,
            "extra": ExtraArgs,
        }


def test_s3_storage_keeps_objects_private_and_returns_cdn_url() -> None:
    client = FakeS3Client()
    storage = S3MediaStorage(
        bucket="golt-production-media",
        cdn_base_url="https://media.golt.example",
        client=client,
    )

    stored = storage.store(BytesIO(b"video-bytes"), "uploads/2026/08/test clip.mp4", "video/mp4")

    assert client.upload == {
        "body": b"video-bytes",
        "bucket": "golt-production-media",
        "key": "uploads/2026/08/test clip.mp4",
        "extra": {
            "ContentType": "video/mp4",
            "CacheControl": "public, max-age=31536000, immutable",
        },
    }
    assert stored.url == "https://media.golt.example/uploads/2026/08/test%20clip.mp4"


def test_local_storage_streams_to_nested_path(tmp_path) -> None:
    storage = LocalMediaStorage(str(tmp_path), "/media/files")

    stored = storage.store(BytesIO(b"image-bytes"), "uploads/2026/08/image.png", "image/png")

    assert (tmp_path / "uploads/2026/08/image.png").read_bytes() == b"image-bytes"
    assert stored.url == "/media/files/uploads/2026/08/image.png"
