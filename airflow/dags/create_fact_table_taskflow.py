from airflow.decorators import dag, task
from datetime import timedelta
import pendulum
import os
from airflow.providers.postgres.hooks.postgres import PostgresHook
import great_expectations as gx
from great_expectations.exceptions import DataContextError


POSTGRES_CONN_ID = os.getenv('POSTGRES_CONN_ID', 'retail_pg_conn')


@dag(
    dag_id='create_fact_orders_taskflow',
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=timedelta(minutes=60),
    tags=['minio', 'orders', 'taskflow'],
    schedule="@once"
)
def create_fact_orders_dag():
    
    @task()
    def create_fact_orders():
        sql = """
            DROP TABLE IF EXISTS fact_orders;
            CREATE TABLE fact_orders AS
            SELECT
                o.order_id,
                o.customer_id,
                o.order_status,
                o.order_purchase_timestamp::DATE AS order_date,
                COUNT(DISTINCT i.order_item_id) AS total_items,
                SUM(i.price + i.freight_value) AS total_order_value,
                SUM(p.payment_value) AS total_payment_value,
                AVG(CAST(r.review_score AS FLOAT)) AS avg_review_score
            FROM
                stg_olist_orders_dataset o
            LEFT JOIN stg_olist_order_items_dataset i ON o.order_id = i.order_id
            LEFT JOIN stg_olist_order_payments_dataset p ON o.order_id = p.order_id
            LEFT JOIN stg_olist_order_reviews_dataset r ON o.order_id = r.order_id
            GROUP BY
                o.order_id, o.customer_id, o.order_status, o.order_purchase_timestamp;
        """
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        pg_hook.run(sql)
        print("✅ fact_orders table created successfully.")

    @task()
    def validate_fact_orders():
        # Get Airflow PG connection
        pg_conn = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID).get_connection(POSTGRES_CONN_ID)
        conn_str = f"postgresql+psycopg2://{pg_conn.login}:{pg_conn.password}@{pg_conn.host}:{pg_conn.port}/{pg_conn.schema}"

        # Load GX context
        context = gx.get_context(mode="ephemeral")

        # Register datasource if it doesn't exist
        # try:
        #     datasource = context.get_datasource("retail_postgres_datasource")
        # except DataContextError:
        datasource = context.data_sources.add_postgres(name="retail_postgres_datasource", connection_string=conn_str)

        # Register table asset if it doesn't exist
        # try:
        #     asset = datasource.get_asset("fact_orders")
        # except Exception:
        asset = datasource.add_table_asset(name="fact_orders", table_name="fact_orders")

        # TODO: From quickstart
        batch_definition = asset.add_batch_definition_whole_table("batch definition")
        # batch = batch_definition.get_batch()

        # Register suite if it doesn't exist
        # try:
        #     suite = context.get_expectation_suite("fact_orders_suite")
        # except Exception:
        # suite = context.add_expectation_suite("fact_orders_suite") TODO: Not available with ephemeral context
        suite = context.suites.add(gx.core.expectation_suite.ExpectationSuite(name="fact_orders_suite"))

        # suite.add_expectation(
        #     gx.ExpectationConfiguration(
        #         expectation_type="expect_table_row_count_to_be_between",
        #         kwargs={"min_value": 1},
        #     )
        # )

        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id")
        )

        suite.add_expectation(
	        gx.expectations.ExpectColumnValuesToBeBetween(column="total_items", min_value=0)
	    )

        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(column="total_order_value", min_value=1)
        )
	      
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(column="avg_review_score", min_value=0, max_value=5)
        )


        # Build batch request
        batch_request = asset.build_batch_request()
        # validator = context.get_validator(batch_request=batch_request, expectation_suite=suite)
        # TODO: From quickstart
        validation_definition = context.validation_definitions.add(
            gx.core.ValidationDefinition(
                name="validation definition",
                data=batch_definition,
                suite=suite,
            )
        )
        checkpoint = context.checkpoints.add(
            gx.checkpoint.checkpoint.Checkpoint(
                name="checkpoint", validation_definitions=[validation_definition]
            )
        )

        # Add basic expectations if suite was empty
        # if not suite.expectations:
        #     validator.expect_column_values_to_not_be_null("order_id")
        #     validator.expect_column_values_to_be_between("total_items", min_value=1)
        #     validator.expect_column_values_to_be_between("total_order_value", min_value=0)
        #     validator.save_expectation_suite(discard_failed_expectations=False)

        # Run checkpoint
        # result = context.run_checkpoint(
        #     name="validate_retail_fact_orders_checkpoint",
        #     batch_request=batch_request,
        #     expectation_suite_name="fact_orders_suite",
        # )
        result = checkpoint.run()
        print(result.describe())

        if not result.success:
            raise ValueError("❌ Validation failed!")
        else:
            print("✅ fact_orders validated successfully!")

    create_fact_orders() >> validate_fact_orders()

create_fact_orders_dag()
