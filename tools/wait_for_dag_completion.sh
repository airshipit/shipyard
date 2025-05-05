#!/bin/bash

AIRFLOW_PROCESSES=(
    "airflow scheduler"
    "airflow celery worker"
)
AIRFLOW_LOG_FILES=(
    "./scheduler.log"
    "./celery-worker.log"
)

# Check if DAG name is provided as a parameter
if [[ -z "$1" ]]; then
  echo "Usage: $0 <dag_name>"
  exit 1
fi

DAG_NAME="$1"

# Get the authentication token
TOKEN=$(curl -X "GET" "http://localhost:8080/auth/token" 2>/dev/null | jq -r .access_token)

if [[ -z "$TOKEN" ]]; then
  echo "Error: Unable to get authentication token."
  exit 1
fi

echo "Checking running DAGs for DAG name: $DAG_NAME"

# Function to get running DAG runs and their tasks
get_running_dags_and_tasks() {
  RUNNING_DAGS=$(curl -X "GET" "http://localhost:8080/api/v2/dags/$DAG_NAME/dagRuns?state=running" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    2>/dev/null | jq '.dag_runs[]? | {dag_run_id: .dag_run_id, state: .state}')

  if [[ -z "$RUNNING_DAGS" ]]; then
    return 0 # No running DAGs
  else
    echo "Running DAG runs and tasks:"
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
    return 1 # Still running DAGs
  fi
}

get_logs() {
  # Get the folder from the parameter
  FOLDER_TO_SEARCH="$HOME/airflow/logs/update_software"

  # Define the separator
  SEPARATOR="=========================================="

  # Check if the provided folder exists
  if [[ ! -d "$FOLDER_TO_SEARCH" ]]; then
      echo "The folder '$FOLDER_TO_SEARCH' does not exists yet."
  fi

  # Find all log files in the folder and its subdirectories
  LOG_FILES=$(find "$FOLDER_TO_SEARCH" -type f -name "*.log" -not -path "*/dag-processor/*")

  # Check if any log files were found
  if [[ -z "$LOG_FILES" ]]; then
      echo "No log files found in the folder '$FOLDER_TO_SEARCH'."
  fi

  # Iterate through each log file and print its content with separators
  for LOG_FILE in $LOG_FILES; do
      echo "$SEPARATOR"
      echo "Contents of: $LOG_FILE"
      echo "$SEPARATOR"
      cat "$LOG_FILE"
      echo ""
  done

  for i in "${!AIRFLOW_LOG_FILES[@]}"; do
      if [[ -f "${AIRFLOW_LOG_FILES[$i]}" ]]; then
          # Print the logs
          echo "---------------------------------"
          echo "Logs for process ${AIRFLOW_PROCESSES[$i]} $((i + 1)):"
          echo "---------------------------------"
          cat "${AIRFLOW_LOG_FILES[$i]}"
          echo "================================="
      else
          echo "Logs for process ${AIRFLOW_PROCESSES[$i]} now found."
      fi
  done

}

# Loop until there are no running DAGs
while true; do
  if get_running_dags_and_tasks; then
    echo "No running DAGs found for DAG name: $DAG_NAME"
    break
  else
    echo "DAGs are still running... waiting for 5 seconds."
    get_logs
    sleep 5
  fi
done
echo "All DAGs have completed."
