# Use the official Superset base image
FROM apache/superset:latest

# Install psycopg2-binary for PostgreSQL connectivity
# psycopg2-binary is recommended for simpler installation in Docker environments
# Also install sqlalchemy-utils which is often a dependency for database URI parsing
# and python-dotenv if you plan to use .env files inside the container for some reason
# (though for docker-compose, environment variables are usually passed directly)
USER root
RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy-utils

# Switch back to the superset user
USER superset

# You can add any other custom configurations or plugins here if needed
# For example, if you have custom Superset plugins, you would copy them here:
# COPY ./superset_config.py /app/pythonpath/superset_config.py
# COPY ./plugins /app/superset_home/plugins

# The default entrypoint will handle running Superset
