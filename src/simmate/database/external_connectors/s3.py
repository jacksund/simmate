# -*- coding: utf-8 -*-

import warnings
from pathlib import Path

import boto3
from botocore.config import Config
from rich.progress import track


class S3Bucket:
    """
    A simple wrapper around boto3's S3 client.

    Subclass this and set the class-level attributes to configure the connection.
    The original boto3 client is accessible via the `client` property.

    #### Example

    ```python
    class MyBucket(S3Bucket):
        bucket = "my-bucket-name"
        access_key = "..."
        secret_key = "..."
        endpoint_url = "https://s3.amazonaws.com"  # optional
    ```
    """

    bucket: str = None
    access_key: str = None
    secret_key: str = None
    endpoint_url: str = None
    region: str = None
    verify: bool = True
    signature_version: str = None

    @classmethod
    @property
    def client(cls):
        kwargs = {}
        if cls.access_key:
            kwargs["aws_access_key_id"] = cls.access_key
        if cls.secret_key:
            kwargs["aws_secret_access_key"] = cls.secret_key
        if cls.endpoint_url:
            kwargs["endpoint_url"] = cls.endpoint_url
        if cls.region:
            kwargs["region_name"] = cls.region
        if cls.signature_version:
            kwargs["config"] = Config(signature_version=cls.signature_version)
        kwargs["verify"] = cls.verify

        if not cls.verify:
            warnings.filterwarnings("ignore")

        return boto3.client("s3", **kwargs)

    @classmethod
    def list_keys(
        cls,
        bucket: str = None,
        prefix: str = "",
        suffix: str = None,
    ) -> list[str]:
        """
        Lists all non-directory object keys in a bucket/prefix.

        #### Parameters

        - `bucket`:
            The S3 bucket to list. Defaults to `cls.bucket`.
        - `prefix`:
            Key prefix to filter by (e.g. "my/folder").
        - `suffix`:
            If provided, only keys ending with this string are returned
            (e.g. ".bz2").
        """
        bucket = bucket or cls.bucket
        client = cls.client
        paginator = client.get_paginator("list_objects_v2")
        keys = [
            obj["Key"]
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
            if not obj["Key"].endswith("/")
        ]
        if suffix is not None:
            keys = [k for k in keys if k.endswith(suffix)]
        return keys

    @classmethod
    def upload_directory(
        cls,
        local_dir: Path | str,
        s3_prefix: str = "",
    ) -> None:
        """
        Recursively uploads all files in a local directory to the S3 bucket.

        Files already present in S3 (by key) are skipped, making this safe to
        re-run for interrupted uploads.

        #### Parameters

        - `local_dir`:
            Local directory whose contents will be uploaded.
        - `s3_prefix`:
            Key prefix within the bucket (e.g. "my/folder"). No leading slash.
        """
        local_dir = Path(local_dir)
        client = cls.client

        existing_keys = set()
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=cls.bucket, Prefix=s3_prefix):
            for obj in page.get("Contents", []):
                existing_keys.add(obj["Key"])

        local_files = [p for p in local_dir.rglob("*") if p.is_file()]

        for local_path in track(local_files, description="Uploading to S3..."):
            relative = local_path.relative_to(local_dir)
            s3_key = f"{s3_prefix}/{relative}".lstrip("/").replace("\\", "/")
            if s3_key not in existing_keys:
                client.upload_file(str(local_path), cls.bucket, s3_key)

    @classmethod
    def sync_directory(
        cls,
        local_dir: Path | str,
        s3_prefix: str = "",
        bucket: str = None,
    ) -> Path:
        """
        Recursively downloads all files from a bucket prefix to a local directory.

        Files already present locally are skipped, making this safe to re-run
        for interrupted syncs.

        #### Parameters

        - `local_dir`:
            Local directory to sync files into. Created if it does not exist.
        - `s3_prefix`:
            Key prefix within the bucket to sync from (e.g. "my/folder"). No
            leading slash.
        - `bucket`:
            The S3 bucket to sync from. Defaults to `cls.bucket`.

        #### Returns

        - `local_dir`:
            The path to the local directory as a `pathlib.Path` object.
        """
        from simmate.utils.files import get_directory

        local_dir = get_directory(local_dir)
        bucket = bucket or cls.bucket
        client = cls.client

        all_keys = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=s3_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/"):
                    all_keys.append(key)

        for s3_key in track(all_keys, description="Syncing from S3..."):
            relative = s3_key[len(s3_prefix) :].lstrip("/")
            local_path = local_dir / relative
            if not local_path.exists():
                local_path.parent.mkdir(parents=True, exist_ok=True)
                client.download_file(bucket, s3_key, str(local_path))

        return local_dir
