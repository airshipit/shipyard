#!/bin/bash
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

set -ex

# NOTE: We are directing all the output of the script to /dev/null in order
# to complete the workflow. Hence it will be useful to create a log file to
# track the progress of the script for troubleshooting purpose.
check_timeout_counter() {

    # Check total elapsed time
    # The default time out is set to 5 minutes
    if [[ $counter -ge $max_count ]]; then
        echo -e "Update Site Workflow Status Check Timed Out!" >> /usr/local/airflow/upgrade_airflow_worker.log
        return 1
    fi
}

# Define Variables
#
# Allow user to optionally pass in custom query time and max count as $4
# and $5 respectively
# Default query time is 30 seconds
# Default max_count for 5 minutes time out is 60*5/30 = 10
#
# NOTE: Dag ID will take value of $1
#
# NOTE: $2 will look like '2018-03-13' while $3 will look like '05:10:19'
# The execution date that we need to pass into the Airflow CLI will need
# to take the form of '2018-03-13T05:10:19'. Hence we will need to concatenate
# $2 and $3 together to form the dag_execution_date.
#
dag_id=$1
dag_execution_date="$2T$3"
query_time=${4:-30}
max_count=${5:-10}

# Initialize dag_state to "running" state
# Dag can be in "running", "success", "failed", "skipped" or "up for retry" state
dag_state="running"

# Initialize counter to 1
counter=1

echo -e "Checking Dag State..."
while true;
do
    # Set current working directory to be the directory where the shell script
    # is located. In this way we will be able to import the modules that are
    # required for our custom Operators.
    cd "${0%/*}"

    # Get current state of dag using Airflow CLI
    # Use grep to remove logging messages that can pollute the status response
    check_dag_state=$(airflow dags state ${dag_id} ${dag_execution_date} | grep -vE "DEBUG|INFO|WARN|ERROR")
    echo -e ${check_dag_state} >> /usr/local/airflow/upgrade_airflow_worker.log

    # We will need to extract the last word in the 'check_dag_state'
    # string variable as that will contain the status of the dag run
    dag_state=$(echo ${check_dag_state} | awk -F ',' '{print $1}')
    echo -e ${dag_state} >> /usr/local/airflow/upgrade_airflow_worker.log

    if [[ $dag_state == "success" ]]; then
        echo -e "\nWorkflow has completed" >> /usr/local/airflow/upgrade_airflow_worker.log
        echo -e "\n" >> /usr/local/airflow/upgrade_airflow_worker.log
        echo -e "Proceeding to upgrade Airflow Worker..." >> /usr/local/airflow/upgrade_airflow_worker.log
        echo -e "Deleting Airflow Worker Pods..." >> /usr/local/airflow/upgrade_airflow_worker.log

        # Delete Airflow Worker pod so that they will respawn with the new
        # configurations and/or images

        # Get the name of the current pod
        CURRENT_POD=$(hostname)

        # Loop through all pods matching the 'airflow-worker' pattern, excluding the current pod
        for i in $(kubectl get pods -n ucp | grep -i airflow-worker | awk '{print $1}' | grep -v $CURRENT_POD); do
            kubectl delete pod $i -n ucp
        done

        # Finally, delete the current pod
        kubectl delete pod $CURRENT_POD -n ucp


        echo -e "Airflow Worker Pods Deleted!" >> /usr/local/airflow/upgrade_airflow_worker.log

        return 0
    fi

    echo -e "Workflow is in" $dag_state "state\n" >> /usr/local/airflow/upgrade_airflow_worker.log
    echo -e "Back Off for $query_time seconds...\n" >> /usr/local/airflow/upgrade_airflow_worker.log
    sleep $query_time

    # Step counter and check the timeout counter
    ((counter++))
    check_timeout_counter
done
