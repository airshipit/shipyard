#!/bin/bash
# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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

set -x

# Note that we will need to execute the deckhand_load_yaml
# script first before the deploy_site script
# Check to ensure that the Shipyard CLI has been installed on
# the Genesis host during the deckhand YAML load phase. Exit
# script if Shipyard CLI is not installed.
command -v shipyard >/dev/null 2>&1 || { echo >&2 "Please install Shipyard CLI before executing the script."; exit 1; }

# Define Namespace
namespace="ucp"

# Initialize Variables with Default Values
# Note that 'query_time' has a default value of 90 seconds
# Note that 'deploy_timeout' has a default value of 60 loops (based on
# 90 seconds back off per cycle, i.e. 60 * 90 = 5400 seconds = 1.5 hrs)
query_time=90
deploy_timeout=60
OS_USER_DOMAIN_NAME="default"
OS_PROJECT_DOMAIN_NAME="default"
OS_PROJECT_NAME="service"
OS_USERNAME="shipyard"
OS_PASSWORD="password"
OS_AUTH_URL="http://keystone.${namespace}:80/v3"

# Override OpenStack Environment Variables, query_time and
# deploy_timeout if need be
# For instance, we can run the script in the following manner:
#
# $ ./deploy_site.sh -q 110 -t 120 -u SY -p supersecret -d test -D test -n admin -l http://keystone.test:80/v3
#
# This will set the variables to the following values:
#
#    - query_time=110
#    - deploy_timeout=120
#    - OS_USERNAME=SY
#    - OS_PASSWORD=supersecret
#    - OS_USER_DOMAIN_NAME=test
#    - OS_PROJECT_DOMAIN_NAME=test
#    - OS_PROJECT_NAME=admin
#    - OS_AUTH_URL=http://keystone.test:80/v3
#
while getopts q:t:u:p:d:D:n:l: option
do
 case "${option}"
 in
 q) query_time=${OPTARG};;
 t) deploy_timeout=${OPTARG};;
 u) OS_USERNAME=${OPTARG};;
 p) OS_PASSWORD=${OPTARG};;
 d) OS_USER_DOMAIN_NAME=${OPTARG};;
 D) OS_PROJECT_DOMAIN_NAME=${OPTARG};;
 n) OS_PROJECT_NAME=${OPTARG};;
 l) OS_AUTH_URL=${OPTARG};;
 esac
done

# Export Environment Variables
export OS_USER_DOMAIN_NAME=${OS_USER_DOMAIN_NAME}
export OS_PROJECT_DOMAIN_NAME=${OS_PROJECT_DOMAIN_NAME}
export OS_PROJECT_NAME=${OS_PROJECT_NAME}
export OS_USERNAME=${OS_USERNAME}
export OS_PASSWORD=${OS_PASSWORD}
export OS_AUTH_URL=${OS_AUTH_URL}

# Define Color
NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'

# Execute deploy_site
echo -e "Execute deploy_site Dag...\n"
shipyard create action deploy_site

# The status or lifecycle phase of an action can be
#
# 1) Pending - The action is scheduled or preparing for execution.
# 2) Processing - The action is underway.
# 3) Complete - The action has completed successfully.
# 4) Failed - The action has encountered an error, and has failed.
# 5) Paused - The action has been paused by a user.
# 6) Unknown (*) - Unknown State for corner cases
# 7) null - We will end up with a `null` response from Shipyard if we
#           query the status of the task with an expired keystone token.
#           Note that this should never happen if we use Shipyard CLI as
#           new token is retrieved each time. Description for state 'null'
#           is included here for information only.
#
# Print current list of actions in Shipyard
shipyard get actions

# Retrieve the ID of the 'deploy_site' action that is currently being executed
echo -e "Retrieving Action ID...\n"
action_id=`shipyard get actions | grep deploy_site | grep -i Processing | awk '{print $2}'`

echo "The Action ID is" ${action_id}
echo

# Initialize 'action_lifecycle' to 'Pending'
action_lifecycle="Pending"

# Polling for 'deploy_site' action
deploy_counter=1

check_timeout_counter() {

    # Check total elapsed time
    # The default time out is set to 1.5 hrs
    # This value can be changed by setting $2
    if [[ $deploy_counter -eq $deploy_timeout ]]; then
        echo 'Deploy Site task has timed out.'
        break
    fi
}

while true;
do
    # Get Current State of Action Lifecycle
    shipyard describe ${action_id} > /tmp/get_action_status
    action_lifecycle=`cat /tmp/get_action_status | grep Lifecycle | awk '{print $2}'`

    # Print output of Shipyard CLI
    cat /tmp/get_action_status

    if [[ $action_lifecycle == "Complete" ]]; then
        echo -e '\nSite Successfully Deployed\n'
        break
    fi

    # Check Dag state
    if [[ $action_lifecycle == "Failed" ]] || [[ $action_lifecycle == "Paused" ]] || \
       [[ $action_lifecycle == "Unknown"* ]] || [[ $action_lifecycle == "null" ]]; then
        echo -e "Dag Execution is in" ${RED}$action_lifecycle${NC} "state\n"
        break
    else
        echo -e "Dag Execution is in" ${GREEN}$action_lifecycle${NC} "state\n"

        # Back off between each iteration
        echo -e "Back Off for $query_time seconds...\n"
        sleep $query_time

        # Step counter and check if deployment has timed out
        ((deploy_counter++))
        check_timeout_counter
    fi
done

# Delete the temporary file
rm /tmp/get_action_status

# Return exit code so that we can use it to determine the final
# state of the workflow
if [[ $action_lifecycle == "Complete" ]]; then
    exit 0
else
    exit 1
fi
