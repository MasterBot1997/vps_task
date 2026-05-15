import boto3
from botocore.config import Config
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

s3 = boto3.client(
    's3',
    endpoint_url='https://s3.ru1.storage.beget.cloud',
    aws_access_key_id='',
    aws_secret_access_key='',
    region_name='ru1',
    config=Config(
        request_checksum_calculation='when_required',
        response_checksum_validation='when_required',
    )
)

BUCKET = ''
data = b'A' * 5 * 1024 * 1024  # 5 MB
sha256_hash = hashlib.sha256(data).hexdigest()

def create_incomplete_upload(i):
    key = f'incomplete-upload/test-file-{i:04d}.txt'
    try:
        resp = s3.create_multipart_upload(Bucket=BUCKET, Key=key)
        upload_id = resp['UploadId']

        s3.upload_part(
            Bucket=BUCKET,
            Key=key,
            PartNumber=1,
            UploadId=upload_id,
            Body=data,
            ChecksumSHA256=sha256_hash,
        )
        return f"[OK] {i:04d} — {key}"
    except Exception as e:
        return f"[ERR] {i:04d} — {e}"

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(create_incomplete_upload, i): i for i in range(1, 101)}
    for future in as_completed(futures):
        print(future.result())

print("\nГотово — 100 незавершённых загрузок созданы!")
