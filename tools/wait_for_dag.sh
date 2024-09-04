#!/bin/bash
while true; do
    is_active=$(airflow dags details example_bash_operator -o plain | grep is_active | awk '{print $2}')
    if [ "$is_active" == "True" ]; then
        echo "DAG example_bash_operator is active."
        break
    fi
    echo "Waiting for DAG example_bash_operator to become active..."
    sleep 10
done