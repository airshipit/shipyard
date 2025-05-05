#!/bin/bash
#
# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

cmd=$1
python3_path=$(which python3)
airflow_path=$(which airflow)

# Initialize Airflow DB
if [[ $cmd == 'db init' ]]; then
    ${python3_path} ${airflow_path} db migrate
# Start the services based on argument from Airflow Helm Chart
elif [[ $cmd == 'webserver' ]]; then
    # Start Airflow Webserver
    ${python3_path} ${airflow_path} api-server --pid=/tmp/airflow-api-server.pid
elif [[ $cmd == 'flower' ]]; then
    # Start Airflow Celery Flower
    ${python3_path} ${airflow_path} celery flower --pid=/tmp/airflow-flower.pid
elif [[ $cmd == 'worker' ]]; then
    # Start Airflow Celery Worker
    ${python3_path} ${airflow_path} celery worker --pid=/tmp/airflow-worker.pid
# If command contains the word 'scheduler'
elif [[ $cmd == *scheduler* ]]; then
    while true; do
        # Start Airflow Scheduler
        # $2 and $3 will take on values '-n' and '-1' respectively
        # The value '-1' indicates that the airflow scheduler will run
        # continuously.  Any other value will mean that the scheduler will
        # terminate and restart after x seconds.
        ${python3_path} ${airflow_path} scheduler $2 $3
    done
# If command contains the word 'processor'
elif [[ $cmd == *dag_processor* ]]; then
    while true; do
        # Start Airflow DAG Processor
        # $2 and $3 will take on values '-n' and '-1' respectively
        # The value '-1' indicates that the airflow processor will run
        # continuously.  Any other value will mean that the processor will
        # terminate and restart after x seconds.
        ${python3_path} ${airflow_path} dag-processor $2 $3
    done
elif [[ $cmd == 'log_monitor' ]]; then
    echo "======================================================================"
    echo "Monitoring folder: $LOGROTATE_PATH"
    echo "======================================================================"

    # Define the separator
    SEPARATOR="=========================================="

    # Check if the provided folder exists
    if [[ ! -d "$LOGROTATE_PATH" ]]; then
    echo "Folder '$LOGROTATE_PATH' does not exist."
    fi

# Function to find and print log files
print_logs() {
    LOG_FILES=$(find "$LOGROTATE_PATH" -type f -name "*.log" \
        -newermt "-60 seconds")

    if [[ -z "$LOG_FILES" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') No new log files found \
in the folder '$LOGROTATE_PATH'."
    else
        for LOG_FILE in $LOG_FILES; do
            echo "$SEPARATOR"
            echo "Contents of: $LOG_FILE"
            echo "$SEPARATOR"
            cat "$LOG_FILE"
            echo ""
        done
    fi
}



# Function to get running DAG runs and their tasks for all DAGs
get_running_dags_and_tasks_all() {
  TOKEN=$(curl -X "GET" "http://localhost:8080/auth/token" 2>/dev/null | jq -r .access_token)

  if [[ -z "$TOKEN" ]]; then
    echo "Error: Unable to get authentication token."
    return 0
  fi

  # Get all DAG names
  DAG_NAMES=$(curl -X "GET" "http://localhost:8080/api/v2/dags" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    2>/dev/null | jq -r '.dags[]?.dag_id')

  if [[ -z "$DAG_NAMES" ]]; then
    echo "No DAGs found."
    return 1
  fi

  for DAG_NAME in $DAG_NAMES; do
    RUNNING_DAGS=$(curl -X "GET" "http://localhost:8080/api/v2/dags/$DAG_NAME/dagRuns" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      2>/dev/null | jq '.dag_runs[]? | {dag_run_id: .dag_run_id, state: .state}')

    if [[ -z "$RUNNING_DAGS" ]]; then
      return 1 # No running DAGs for this DAG
    else
      echo "Running DAG runs and tasks for DAG: $DAG_NAME"
      echo "$RUNNING_DAGS" | jq -r '.dag_run_id' | while read -r DAG_RUN_ID; do
        echo "DAG Run ID: $DAG_RUN_ID"
        echo "Tasks for this DAG Run:"
        curl -X "GET" "http://localhost:8080/api/v2/dags/$DAG_NAME/dagRuns/$DAG_RUN_ID/taskInstances" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          2>/dev/null | jq -r '.task_instances[]? | "Task: \(.task_id), State: \(.state)"'
        echo "-----------------------------------------"

        # Fetch task instances for the current DAG run
        TASKS=$(curl -X "GET" "http://localhost:8080/api/v2/dags/$DAG_NAME/dagRuns/$DAG_RUN_ID/taskInstances" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          2>/dev/null | jq -r '.task_instances[]?.task_id')

        if [[ -z "$TASKS" ]]; then
          echo "No tasks found for DAG Run ID: $DAG_RUN_ID"
        else
          echo "$TASKS" | while read -r TASK_ID; do
            echo "Task: $TASK_ID"

            # Fetch XCom values for the current task
            echo "Fetching XCom values for task '$TASK_ID' in DAG Run ID: $DAG_RUN_ID"
            XCOM_RESPONSE=$(curl -X "GET" "http://localhost:8080/api/v2/dags/$DAG_NAME/dagRuns/$DAG_RUN_ID/taskInstances/$TASK_ID/xcomEntries" \
              -H "Authorization: Bearer $TOKEN" \
              -H "Content-Type: application/json" \
              2>/dev/null)

            # Check if the response is valid JSON and parse it
            if echo "$XCOM_RESPONSE" | jq empty 2>/dev/null; then
              echo "$XCOM_RESPONSE" | jq
            else
              echo "No XCom values found or unexpected response for task '$TASK_ID': $XCOM_RESPONSE"
            fi
            echo "-----------------------------------------"
          done
        fi
      done
    fi
  done
  return 0
}



    # Eternal loop to continuously check for new log files and print their contents
    sleep 10
    while true; do
        get_running_dags_and_tasks_all
        print_logs
        echo "Sleeping for 30 seconds before checking for new logs..."
        sleep 30
    done
elif [[ $cmd == 'quicktest' ]]; then
    ${python3_path} ${airflow_path} version
    ${python3_path} ${airflow_path} db migrate
    ${python3_path} ${airflow_path} dag-processor >/dev/null 2>&1  &
    while true; do
        is_paused=$(${python3_path} ${airflow_path} dags details example_branch_labels -o plain | grep is_paused | awk '{print $2}')
        if [ "$is_paused" == "True" ]; then
            echo "DAG processor is running!"
            break
        fi
        echo "Waiting for DAG processor to become active..."
        sleep 10
    done
    ${python3_path} ${airflow_path} dags list
    ${python3_path} ${airflow_path} dags list-import-errors
    ${python3_path} ${airflow_path} dags unpause example_branch_labels
    while true; do
        is_paused=$(${python3_path} ${airflow_path} dags details example_branch_labels -o plain | grep is_paused | awk '{print $2}')
        if [ "$is_paused" == "False" ]; then
            echo "DAG example_branch_labels is active."
            break
        fi
        echo "Waiting for DAG example_branch_labels to become active..."
        sleep 10
    done
    ${python3_path} ${airflow_path} dags test example_branch_labels
    ${python3_path} ${airflow_path} dags list-runs example_branch_labels
    RUN_ID=$(${python3_path} ${airflow_path} dags list-runs example_branch_labels -o plain | grep example_branch_labels | awk '{print $2}')
    ${python3_path} ${airflow_path} tasks states-for-dag-run example_branch_labels ${RUN_ID}
    RUN_ID=$(${python3_path} ${airflow_path} dags list-runs example_branch_labels -o plain | grep example_branch_labels | awk '{print $2}')
    ${python3_path} ${airflow_path} dags state example_branch_labels ${RUN_ID}
else
     echo "Invalid Command!"
     exit 1
fi
