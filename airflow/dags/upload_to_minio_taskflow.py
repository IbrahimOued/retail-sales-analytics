# dags/upload_to_minio_taskflow.py
from airflow.decorators import dag, task
from datetime import datetime, timedelta
import boto3
import os

from dotenv import load_dotenv
load_dotenv()

# Load environment variables
BUCKET_NAME = os.getenv('BUCKET_NAME', 'retail')
LOCAL_FOLDER = os.getenv('LOCAL_FOLDER', '/opt/airflow/datasets/')  # docker-mount this
S3_PREFIX = os.getenv('S3_PREFIX', 'raw/')
ENDPOINT_URL = os.getenv('ENDPOINT_URL', 'http://minio:9000')  # Docker service name
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'ibra')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '123456seven')



@dag(
    dag_id='upload_to_minio_taskflow',
    start_date=datetime.now() - timedelta(days=1),
    catchup=False,
    tags=['taskflow', 'minio'],
    schedule="@once"  # or "@daily", etc.
)
def upload_to_minio_taskflow():

    @task()
    def ensure_bucket():
        s3 = boto3.client(
            's3',
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        existing_buckets = [b['Name'] for b in s3.list_buckets().get('Buckets', [])]
        if BUCKET_NAME not in existing_buckets:
            s3.create_bucket(Bucket=BUCKET_NAME)
            print(f"Bucket {BUCKET_NAME} created.")
        else:
            print(f"Bucket {BUCKET_NAME} already exists.")

    @task()
    def list_local_csvs() -> list:
        files = [f for f in os.listdir(LOCAL_FOLDER) if f.endswith('.csv')]
        print(f"Found {len(files)} CSV files: {files}")
        return files

    @task()
    def upload_file_to_minio(file_name: str):
        s3 = boto3.client(
            's3',
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        file_path = os.path.join(LOCAL_FOLDER, file_name)
        s3.upload_file(file_path, BUCKET_NAME, f"{S3_PREFIX}{file_name}")
        print(f"Uploaded {file_name} to s3://{BUCKET_NAME}/{S3_PREFIX}{file_name}")

    ensure_bucket()
    csv_files = list_local_csvs()

    # Dynamic task mapping using expand
    upload_file_to_minio.expand(file_name=csv_files)

upload_to_minio_taskflow()