#!/bin/bash
while true; do
    is_active=$(airflow dags details example_branch_labels -o plain | grep is_active | awk '{print $2}')
    if [ "$is_active" == "True" ]; then
        echo "DAG example_branch_labels is active."
        break
    fi
    echo "Waiting for DAG example_branch_labels to become active..."
    sleep 10
done