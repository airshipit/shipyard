#!/bin/bash
while true; do
    is_paused=$(airflow dags details example_bash_operator -o plain | grep is_paused | awk '{print $2}')
    if [ "$is_paused" == "True" ]; then
        echo "DAG processor is running!"
        break
    fi
    echo "Waiting for DAG processor to become active..."
    sleep 10
done