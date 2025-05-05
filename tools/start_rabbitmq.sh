#!/bin/bash
set -x

# Stop and remove any existing RabbitMQ container
if [[ ! -z $(docker ps | grep 'rabbitmq_integration') ]]
then
  docker stop 'rabbitmq_integration'
fi

# Start a new RabbitMQ container
docker run --rm -dp 5672:5672 -dp 15672:15672 --name 'rabbitmq_integration' \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin \
  quay.io/airshipit/rabbitmq:3.10.18-management

# Wait for RabbitMQ to initialize
sleep 15

# Add the airflow user with password
docker exec -it rabbitmq_integration rabbitmqctl add_user airflow password

# Set permissions for the airflow user
docker exec -it rabbitmq_integration rabbitmqctl set_permissions -p / airflow ".*" ".*" ".*"

# Verify RabbitMQ is running and the user is added
docker exec -it rabbitmq_integration rabbitmqctl list_users
