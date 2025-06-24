# FROM apache/airflow:2.8.1-python3.10
FROM apache/airflow:latest-python3.12

USER root
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    && apt-get clean

# Switch to the airflow user before running pip install
USER airflow
RUN pip install -U pip
RUN pip install mysqlclient \
    apache-airflow-providers-postgres \
    apache-airflow-providers-mysql

# Install the required packages for the Airflow image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
