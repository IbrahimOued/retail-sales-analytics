# from airflow.decorators import dag
# from airflow.operators.trigger_dagrun import TriggerDagRunOperator
# import pendulum

# @dag(
#     dag_id="full_pipeline_dag",
#     start_date=pendulum.datetime(2023, 10, 1, tz="UTC"),
#     schedule="@daily",  # or "@weekly", etc.
#     catchup=False,
#     tags=["full_pipeline", "taskflow", "minio", "postgres"],
# )
# def full_pipeline():
#     trigger_etl = TriggerDagRunOperator(
#         task_id="trigger_etl_dag",
#         trigger_dag_id="etl_minio_to_postgres_taskflow"
#     )

#     trigger_dim = TriggerDagRunOperator(
#         task_id="trigger_dim_dag",
#         trigger_dag_id="create_dim_tables_taskflow"
#     )

#     trigger_fact = TriggerDagRunOperator(
#         task_id="trigger_fact_dag",
#         trigger_dag_id="create_fact_orders_taskflow"
#     )

#     trigger_etl >> [trigger_dim, trigger_fact]

# full_pipeline()

from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
import pendulum

@dag(
    dag_id="full_pipeline_dag",
    start_date=pendulum.datetime(2023, 10, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["full_pipeline", "taskflow", "minio", "postgres"],
)
def full_pipeline():
    @task
    def start_pipeline():
        return "Starting the full pipeline"

    @task
    def end_pipeline():
        return "Pipeline completed"

    start_task = start_pipeline()

    trigger_etl = TriggerDagRunOperator(
        task_id="trigger_etl_dag",
        trigger_dag_id="etl_minio_to_postgres_taskflow"
    )

    trigger_dim = TriggerDagRunOperator(
        task_id="trigger_dim_dag",
        trigger_dag_id="create_dim_tables_taskflow"
    )

    trigger_fact = TriggerDagRunOperator(
        task_id="trigger_fact_dag",
        trigger_dag_id="create_fact_orders_taskflow"
    )

    end_task = end_pipeline()

    # Define the dependencies
    start_task >> trigger_etl >> [trigger_dim, trigger_fact] >> end_task

full_pipeline()
