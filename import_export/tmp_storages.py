import os
import tempfile
from uuid import uuid4

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class BaseStorage:

    def __init__(self, name=None):
        self.name = name

    def save(self, data, mode='w'):
        raise NotImplementedError

    def read(self, read_mode='r'):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError


class TempFolderStorage(BaseStorage):

    def open(self, mode='r'):
        if self.name:
            return open(self.get_full_path(), mode)
        else:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.name = tmp_file.name
            return tmp_file

    def save(self, data, mode='w'):
        with self.open(mode=mode) as file:
            file.write(data)

    def read(self, mode='r'):
        with self.open(mode=mode) as file:
            return file.read()

    def remove(self):
        os.remove(self.get_full_path())

    def get_full_path(self):
        return os.path.join(
            tempfile.gettempdir(),
            self.name
        )


class CacheStorage(BaseStorage):
    """
    By default memcache maximum size per key is 1MB, be careful with large files.
    """
    CACHE_LIFETIME = 86400
    CACHE_PREFIX = 'django-import-export-'

    def save(self, data, mode=None):
        if not self.name:
            self.name = uuid4().hex
        cache.set(self.CACHE_PREFIX + self.name, data, self.CACHE_LIFETIME)

    def read(self, read_mode='r'):
        return cache.get(self.CACHE_PREFIX + self.name)

    def remove(self):
        cache.delete(self.name)


class MediaStorage(BaseStorage):
    MEDIA_FOLDER = 'django-import-export'

    def save(self, data, mode=None):
        if not self.name:
            self.name = uuid4().hex
        default_storage.save(self.get_full_path(), ContentFile(data))

    def read(self, read_mode='rb'):
        with default_storage.open(self.get_full_path(), mode=read_mode) as f:
            return f.read()

    def remove(self):
        default_storage.delete(self.get_full_path())

    def get_full_path(self):
        return os.path.join(
            self.MEDIA_FOLDER,
            self.name
        )
import boto3
import io
from uuid import uuid4
from django.conf import settings

class S3Storage:

    def __init__(self, name=None):
        self.name = name
        # import ipdb; ipdb.set_trace()
        session = boto3.session.Session()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # self.s3_client = session.resource(
        #     's3',
        #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        # )
        # for bucket in s3.buckets.all():
        #     print(bucket.name)
        # self.bucket = s3.Bucket("import-export-csv")
        # self.s3_client = boto3.client(
        #     's3',
        #     aws_access_key_id=settings.AWS_SECRET_ACCESS_KEY,
        #     aws_secret_access_key=settings.AWS_ACCESS_KEY_ID
        # )
    def save(self, data, mode='w'):

        f = io.BytesIO(data)
        if self.name is None:
            self.name = uuid4().hex
        # import ipdb; ipdb.set_trace()
        self.s3_client.upload_fileobj(f, "import-export-csv", self.name)

    def read(self, read_mode='r'):
        f = io.BytesIO()
        self.s3_client.download_fileobj("import-export-csv", self.name, f)
        # content = f.read()
        # import ipdb; ipdb.set_trace()
        # return content
        f.seek(0)
        return f.read()

    def remove(self):
        # import ipdb; ipdb.set_trace()
        # import ipdb; ipdb.set_trace()
        self.s3_client.delete_object(Bucket="import-export-csv", Key=self.name)
