# Stop the docker compose
#!/bin/bash
# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose could not be found. Please install it first."
    exit 1
fi
# Check if the docker-compose.yml or docker-compose.yaml file exists
if [ ! -f docker-compose.yml ] && [ ! -f docker-compose.yaml ]; then
    echo "docker-compose.yml or docker-compose.yaml file not found in the current directory."
    exit 1
fi

# Stop the docker containers
docker-compose down
# Check if the containers stopped successfully
if [ $? -ne 0 ]; then
    echo "Failed to stop docker containers. Please check the docker-compose.yml file and try again."
    exit 1
fi
echo "Docker containers stopped successfully."
# Remove the stopped containers
docker rmi retail-sales-analytics-airflow
# Check if the image were removed successfully
if [ $? -ne 0 ]; then
    echo "Failed to remove docker containers. Please check the docker-compose.yml file and try again."
    exit 1
fi
echo "Airflow image removed successfully."