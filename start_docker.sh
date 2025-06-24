# Start docker compose
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
# Start the docker containers
docker-compose up -d
# Check if the containers started successfully
if [ $? -ne 0 ]; then
    echo "Failed to start docker containers. Please check the docker-compose.yml file and try again."
    exit 1
fi
echo "Docker containers started successfully."