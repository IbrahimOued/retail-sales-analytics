from airflow.decorators import dag, task
import pendulum
from datetime import datetime, timedelta
from airflow.providers.postgres.hooks.postgres import PostgresHook

@dag(
    dag_id="create_dim_tables_taskflow",
    start_date=pendulum.datetime(2023, 10, 1, tz="UTC"),
    catchup=False,
    tags=["dimension", "taskflow", "postgres", "minio"],
    schedule="@once"
)
def create_dim_tables_dag():
    # Define the PostgreSQL connection ID.
    # Ensure you have a connection named 'postgres_retail_sales' configured in your Airflow UI
    # (Admin -> Connections) with the appropriate details for your PostgreSQL database.
    # Example:
    # Conn Id: 'retail_pg_conn'
    # Conn Type: 'Postgres'
    # Host: 'postgres' (or your database host)
    # Port: 5432
    # Schema: retail_db (or your database name)
    # Login: retail_user (or your database user)
    # Password: retail_pass (or your database password)
    POSTGRES_CONN_ID = 'retail_pg_conn'

    @task()
    def create_dim_customers():
        sql = """
        DROP TABLE IF EXISTS dim_customers;
        CREATE TABLE dim_customers AS
        SELECT
            customer_id,
            customer_unique_id,
            customer_city,
            customer_state
        FROM stg_olist_customers_dataset;
        """
        # Instantiate the PostgresHook
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        # Execute the SQL query using the hook's run method
        pg_hook.run(sql)
        print("[CREATED] dim_customers table in PostgreSQL")

    @task()
    def create_dim_sellers():
        sql = """
        DROP TABLE IF EXISTS dim_sellers;
        CREATE TABLE dim_sellers AS
        SELECT
            seller_id,
            seller_city,
            seller_state
        FROM stg_olist_sellers_dataset;
        """
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        pg_hook.run(sql)
        print("[CREATED] dim_sellers table in PostgreSQL")

    @task()
    def create_dim_products():
        sql = """
        DROP TABLE IF EXISTS dim_products;
        CREATE TABLE dim_products AS
        SELECT
            p.product_id,
            p.product_category_name,
            t.product_category_name_english,
            p.product_name_lenght,
            p.product_description_lenght,
            p.product_photos_qty,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm
        FROM stg_olist_products_dataset p
        LEFT JOIN stg_product_category_name_translation t
        ON p.product_category_name = t.product_category_name;
        """
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        pg_hook.run(sql)
        print("[CREATED] dim_products table in PostgreSQL")

    @task()
    def create_dim_dates():
        sql = """
        DROP TABLE IF EXISTS dim_dates;
        CREATE TABLE dim_dates AS
        WITH orders_with_casted_timestamp AS (
            SELECT
                -- Cast the original text/varchar column to TIMESTAMP once
                order_purchase_timestamp::TIMESTAMP AS purchase_ts
            FROM stg_olist_orders_dataset
        )
        SELECT DISTINCT
            purchase_ts::DATE AS date,
            EXTRACT(DAY FROM purchase_ts) AS day,
            EXTRACT(MONTH FROM purchase_ts) AS month,
            TO_CHAR(purchase_ts, 'Month') AS month_name,
            EXTRACT(YEAR FROM purchase_ts) AS year,
            EXTRACT(DOW FROM purchase_ts) AS weekday,
            TO_CHAR(purchase_ts, 'Day') AS weekday_name,
            CASE
                WHEN EXTRACT(DOW FROM purchase_ts) IN (0, 6) THEN TRUE
                ELSE FALSE
            END AS is_weekend
        FROM orders_with_casted_timestamp;
        """
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        pg_hook.run(sql)
        print("[CREATED] dim_dates table in PostgreSQL")

    # Define task dependencies
    create_dim_customers_task = create_dim_customers()
    create_dim_sellers_task = create_dim_sellers()
    create_dim_products_task = create_dim_products()
    create_dim_dates_task = create_dim_dates()

    # If these tasks need to run in a specific order (e.g., after staging tables are loaded),
    # you would define dependencies here. For now, they can run in parallel.
    # Example if they depend on each other:
    # create_dim_customers_task >> create_dim_sellers_task

create_dim_tables_dag()
