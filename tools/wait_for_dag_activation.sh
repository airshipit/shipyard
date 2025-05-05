#!/bin/bash
while true; do
    is_paused=$(airflow dags details example_bash_operator -o plain | grep is_paused | awk '{print $2}')
    if [ "$is_paused" == "False" ]; then
        echo "DAG example_bash_operator is active."
        break
    fi
    echo "Waiting for DAG example_bash_operator to become active..."
    sleep 10
done