# -*- coding: utf-8 -*-

import warnings
from pathlib import Path

import boto3
from botocore.config import Config
from rich.progress import track

from simmate.config import settings


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
    def _get_boto_kwargs(cls) -> dict:
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
        return kwargs

    @classmethod
    @property
    def client(cls):
        return boto3.client("s3", **cls._get_boto_kwargs())

    @classmethod
    @property
    def bucket_obj(cls):
        """
        The boto3 resource-level Bucket object for `cls.bucket`.

        Useful for object-level operations (e.g. iterating ObjectSummary,
        copying, tagging) that are not available on the low-level client.
        """
        return boto3.resource("s3", **cls._get_boto_kwargs()).Bucket(cls.bucket)

    @classmethod
    def list_keys(
        cls,
        prefix: str = "",
        suffix: str = None,
    ) -> list[str]:
        """
        Lists all non-directory object keys in a bucket/prefix.

        #### Parameters

        - `prefix`:
            Key prefix to filter by (e.g. "my/folder").
        - `suffix`:
            If provided, only keys ending with this string are returned
            (e.g. ".bz2").
        """
        client = cls.client
        paginator = client.get_paginator("list_objects_v2")
        keys = [
            obj["Key"]
            for page in paginator.paginate(Bucket=cls.bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
            if not obj["Key"].endswith("/")
        ]
        if suffix is not None:
            keys = [k for k in keys if k.endswith(suffix)]
        return keys

    @classmethod
    def list_objects(
        cls,
        prefix: str = "",
        suffix: str = None,
    ) -> list:
        """
        Like `list_keys`, but returns boto3 ObjectSummary instances instead of
        key strings.

        Each ObjectSummary exposes `.key`, `.size`, `.last_modified`, and
        `.get()` / `.download_file()` via the resource API.

        #### Parameters

        - `prefix`:
            Key prefix to filter by (e.g. "my/folder").
        - `suffix`:
            If provided, only objects whose key ends with this string are
            returned (e.g. ".bz2").
        """
        objects = [
            obj
            for obj in cls.bucket_obj.objects.filter(Prefix=prefix)
            if not obj.key.endswith("/")
        ]
        if suffix is not None:
            objects = [o for o in objects if o.key.endswith(suffix)]
        return objects

    @classmethod
    def list_contents(
        cls,
        prefix: str = "",
    ) -> dict:
        """
        Lists immediate subfolders and files at a given prefix (one level deep),
        equivalent to running `ls` on a directory.

        Uses the S3 delimiter trick so only one level of hierarchy is returned
        at a time — subfolders are not recursed into.

        #### Parameters

        - `prefix`:
            The folder prefix to inspect (e.g. "my/folder/"). A trailing slash
            is recommended but not required.

        #### Returns

        A dict with two keys:
        - `"folders"`: list of common-prefix strings (e.g. "my/folder/sub/")
        - `"files"`: list of object key strings at this level
        """
        paginator = cls.client.get_paginator("list_objects_v2")
        folders, files = [], []
        for page in paginator.paginate(Bucket=cls.bucket, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                folders.append(cp["Prefix"])
            for obj in page.get("Contents", []):
                if not obj["Key"].endswith("/"):
                    files.append(obj["Key"])
        return {"folders": folders, "files": files}

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

        #### Returns

        - `local_dir`:
            The path to the local directory as a `pathlib.Path` object.
        """
        from simmate.utils.files import get_directory

        local_dir = get_directory(local_dir)
        client = cls.client

        all_keys = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=cls.bucket, Prefix=s3_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/"):
                    all_keys.append(key)

        for s3_key in track(all_keys, description="Syncing from S3..."):
            relative = s3_key[len(s3_prefix) :].lstrip("/")
            local_path = local_dir / relative
            if not local_path.exists():
                local_path.parent.mkdir(parents=True, exist_ok=True)
                client.download_file(cls.bucket, s3_key, str(local_path))

        return local_dir


class SimmateS3Bucket(S3Bucket):
    """
    An S3Bucket configured from the user's ``settings.s3`` block.

    Configure it in your ``settings.yaml`` and then use directly::

        from simmate.database.external_connectors.s3 import SimmateS3Bucket

        SimmateS3Bucket.upload_directory("./my_data", "experiments/run1")
        SimmateS3Bucket.sync_directory("./local_copy", "experiments/run1")
    """

    bucket = settings.s3.bucket
    access_key = settings.s3.access_key
    secret_key = settings.s3.secret_key
    endpoint_url = settings.s3.endpoint_url
    region = settings.s3.region
    verify = settings.s3.verify
    signature_version = settings.s3.signature_version
