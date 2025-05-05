#!/bin/bash

# Define process commands and log file paths
PROCESSES=(
    "airflow dag-processor"
    "airflow api-server"
    "airflow scheduler"
    "airflow celery worker"
)
LOG_FILES=(
    "./dag-processor.log"
    "./api-server.log"
    "./scheduler.log"
    "./celery-worker.log"
)
PID_FILES=(
    "/tmp/dag-processor.pid"
    "/tmp/api-server.pid"
    "/tmp/scheduler.pid"
    "/tmp/celery-worker.pid"
)

# Function to start processes
start_processes() {
    echo "Starting processes..."
    for i in "${!PROCESSES[@]}"; do
        # Start the process and redirect logs
        ${PROCESSES[$i]} > "${LOG_FILES[$i]}" 2>&1 &
        # Save the process ID (PID) to a file
        echo $! > "${PID_FILES[$i]}"
        echo "Started process ${PROCESSES[$i]} $((i + 1)) (PID: $!)"
    done
}

# Function to stop processes and print logs
stop_processes() {
    echo "Stopping processes and displaying logs..."
    for i in "${!PID_FILES[@]}"; do
        if [[ -f "${PID_FILES[$i]}" ]]; then
            # Get the PID from the PID file
            PID=$(cat "${PID_FILES[$i]}")
            # Kill the process
            kill "$PID" 2>/dev/null && echo "Stopped process $((i + 1)) (PID: $PID)"
            # Remove the PID file
            rm -f "${PID_FILES[$i]}"
            # Print the logs
            echo "---------------------------------"
            echo "Logs for process ${PROCESSES[$i]} $((i + 1)) (PID: $PID):"
            echo "---------------------------------"
            cat "${LOG_FILES[$i]}"
            echo "================================="
            # Remove the LOG file
            rm -f "${LOG_FILES[$i]}"
        else
            echo "Process ${PROCESSES[$i]} $((i + 1)) is not running."
        fi
    done
}

stop_postgres() {
    # Stop and remove any existing PostgreSQL container
    if [[ ! -z $(docker ps | grep 'psql_integration') ]]
    then
    docker stop 'psql_integration'
    fi
}

start_postgres() {
    docker run --rm -dp 5432:5432 --name 'psql_integration' -e POSTGRES_HOST_AUTH_METHOD=trust quay.io/airshipit/postgres:14.8
    sleep 15

    docker run --rm --net host quay.io/airshipit/postgres:14.8 psql -h localhost -c "create user airflow with password 'password';" postgres postgres
    docker run --rm --net host quay.io/airshipit/postgres:14.8 psql -h localhost -c "create database airflow;" postgres postgres

}

stop_rabbitmq() {
    # Stop and remove any existing RabbitMQ container
    if [[ ! -z $(docker ps | grep 'rabbitmq_integration') ]]
    then
    docker stop 'rabbitmq_integration'
    fi
}

start_rabbitmq() {
    # Start a new RabbitMQ container
    docker run --rm -dp 5672:5672 -dp 15672:15672 --name 'rabbitmq_integration' \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    quay.io/airshipit/rabbitmq:3.10.18-management

    # Wait for RabbitMQ to initialize
    sleep 15

    # Add the airflow user with password
    docker exec rabbitmq_integration rabbitmqctl add_user airflow password

    # Set permissions for the airflow user
    docker exec rabbitmq_integration rabbitmqctl set_permissions -p / airflow ".*" ".*" ".*"

    # Verify RabbitMQ is running and the user is added
    docker exec rabbitmq_integration rabbitmqctl list_users
}

wait_for_api_server() {
    # URL to check
    URL="http://localhost:8080/auth/token"

    # Timeout in seconds
    TIMEOUT=300
    INTERVAL=5
    ELAPSED=0

    echo "Waiting for API server to be reachable at $URL..."

    while ! curl -i --fail "$URL"; do
        if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
            echo "Timeout reached! API server is not reachable at $URL."
            exit 1
        fi

        echo "API server not reachable yet. Retrying in $INTERVAL seconds..."
        sleep "$INTERVAL"
        ELAPSED=$((ELAPSED + INTERVAL))
    done

    echo "API server is now reachable at $URL."
}

# Check the script's parameter
if [[ "$1" == "start" ]]; then
    env
    stop_rabbitmq
    stop_postgres
    pkill -f 'celeryd: celery'
    pkill -f 'airflow api_server'
    sleep 5
    start_postgres
    start_rabbitmq
    airflow db migrate
    start_processes
    wait_for_api_server
elif [[ "$1" == "stop" ]]; then
    stop_processes
    pkill -f 'celeryd: celery'
    pkill -f 'airflow api_server'
    pkill -f 'airflow dag-processor'
    stop_rabbitmq
    stop_postgres
    echo "All processes stopped."
else
    echo "Usage: $0 {start|stop}"
    exit 1
fi