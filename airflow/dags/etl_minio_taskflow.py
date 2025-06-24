from airflow.decorators import dag, task
import pendulum
import boto3
import pandas as pd
import io
import os
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine

from dotenv import load_dotenv
load_dotenv()


ENDPOINT_URL = os.getenv('ENDPOINT_URL', 'http://minio:9000')  # Docker service name
POSTGRES_CONN_ID = os.getenv('POSTGRES_CONN_ID', 'retail_pg_conn')  # Airflow Connection ID for PostgreSQL
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'ibra')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '123456seven')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'retail')
S3_PREFIX = os.getenv('S3_PREFIX', 'raw/')
FILES = [
    'olist_customers_dataset.csv',
    'olist_geolocation_dataset.csv',
    'olist_order_items_dataset.csv',
    'olist_order_payments_dataset.csv',
    'olist_order_reviews_dataset.csv',
    'olist_orders_dataset.csv',
    'olist_products_dataset.csv',
    'olist_sellers_dataset.csv',
    'product_category_name_translation.csv'
]

# Postgres connection details are now configured as an Airflow Connection
# You should create a PostgreSQL connection in the Airflow UI with:
# Conn Id: 'postgres_retail_sales'
# Conn Type: 'Postgres'
# Host: 'postgres' (or 'localhost' if running locally outside Docker)
# Port: 5432
# Database: retail_sales_db
# User: postgres
# Password: postgres


@dag(
    dag_id='etl_minio_to_postgres_taskflow',
    start_date=pendulum.datetime(2023, 10, 1, tz="UTC"),
    catchup=False,
    tags=['taskflow', 'etl', 'minio', 'postgres', 'hook'],
    schedule="@once",  # or "@daily", etc.
)
def etl_minio_to_postgres():

    @task()
    def extract_from_minio(filename: str) -> str:
        s3 = boto3.client(
            's3',
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_PREFIX + filename)
        content = obj['Body'].read()
        print(f"[EXTRACTED] {filename} from MinIO")
        # Gonna bypass the validation and load the CSV directly into a DataFrame
        df = pd.read_csv(io.BytesIO(content))
        return df
        #return content.decode('utf-8')  # returns CSV string

    @task()
    def validate_csv(df: pd.DataFrame, filename: str) -> pd.DataFrame:
        # df = pd.read_csv(io.StringIO(csv_content))
        #df = pd.read_csv(csv_content)

        if df.shape[0] == 0 or df.shape[1] == 0:
            raise ValueError(f"{filename} is empty or malformed")

        print(f"[VALIDATION PASSED] {filename}: {df.shape[0]} rows, {df.shape[1]} columns")
        return df



    @task()
    def load_to_postgres_hook(df: pd.DataFrame, filename: str):
        # Instantiate PostgresHook using the connection ID
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

        table_name = 'stg_' + filename.replace('.csv', '').lower()

        # Use the get_uri method to get the connection URI
        conn_uri = pg_hook.get_uri()

        # Create a SQLAlchemy engine from the connection URI
        engine = create_engine(conn_uri)

        # Use pandas to_sql method with the engine obtained from the hook
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)

        print(f"[LOADED] {filename} -> {table_name} in PostgreSQL using PostgresHook")

    for file in FILES:
        content = extract_from_minio.override(task_id=f"extract_{file}")(file)
        validated = validate_csv.override(task_id=f"validate_{file}")(content, file)
        load_to_postgres_hook.override(task_id=f"load_{file}")(validated, file)
        # load_to_postgres_hook.override(task_id=f"load_{file}")(content, file) # directly using the dataframe

etl_minio_to_postgres()