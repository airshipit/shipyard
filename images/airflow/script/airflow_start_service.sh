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
    ${python3_path} ${airflow_path} db init
    ${python3_path} ${airflow_path} db migrate
# Start the services based on argument from Airflow Helm Chart
elif [[ $cmd == 'webserver' ]]; then
    ${python3_path} ${airflow_path} webserver
elif [[ $cmd == 'flower' ]]; then
    ${python3_path} ${airflow_path} celery flower --pid=/tmp/airflow-flower.pid
elif [[ $cmd == 'worker' ]]; then
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
elif [[ $cmd == 'quicktest' ]]; then
    ${python3_path} ${airflow_path} version
    ${python3_path} ${airflow_path} db init
    ${python3_path} ${airflow_path} db migrate
    ${python3_path} ${airflow_path} dags list
    ${python3_path} ${airflow_path} scheduler &
    while true; do
        is_active=$(airflow dags details example_bash_operator -o plain | grep is_active | awk '{print $2}')
        if [ "$is_active" == "True" ]; then
            echo "DAG example_bash_operator is active."
            break
        fi
        echo "Waiting for DAG example_bash_operator to become active..."
        sleep 10
    done
    ${python3_path} ${airflow_path} dags list
    ${python3_path} ${airflow_path} dags unpause example_bash_operator
    ${python3_path} ${airflow_path} tasks test example_bash_operator runme_0
    ${python3_path} ${airflow_path} dags backfill example_bash_operator -s 2018-01-01 -e 2018-01-02
    ${python3_path} ${airflow_path} tasks run example_bash_operator runme_0 2018-01-01
    ${python3_path} ${airflow_path} tasks states-for-dag-run example_bash_operator backfill__2018-01-02T00:00:00+00:00
    ${python3_path} ${airflow_path} dags state example_bash_operator 2018-01-01
else
     echo "Invalid Command!"
     exit 1
fi
