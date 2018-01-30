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

# Check to ensure that the Shipyard CLI has been installed on
# the Genesis host during the deckhand YAML load phase. Exit
# script if Shipyard CLI is not installed.
command -v shipyard >/dev/null 2>&1 || { echo >&2 "Please install Shipyard CLI before executing the script."; exit 1; }

# We will need to pass the name of the server that we want to redeploy
# when we execute the script. It is mandatory to do so and the script
# will exit with exception if the server name is missing. For instance,
# we can excute the script in the following manner:
#
# $ ./redeploy_server.sh controller01
#
if [[ -z "$1" ]]; then
    echo -e "Please specify the server name!"
    exit 1
fi

# Define Variables
server=$1
namespace="ucp"

# Initialize Variables
# Note that 'query_time' has a default value of 90 seconds
# Note that 'redeploy_server_max_count' has a default value of 40 loops (based on
# 90 seconds back off per cycle, i.e. 40 * 90 = 3600 seconds = 1 hr)
# Note that user can use a different value for each of the variables by exporting
# the required environment variable prior to running the script
query_time=${query_time:-90}
redeploy_server_max_count=${redeploy_server_max_count:-40}

# Export Environment Variables
export OS_USER_DOMAIN_NAME="${OS_USER_DOMAIN_NAME:-default}"
export OS_PROJECT_DOMAIN_NAME="${OS_PROJECT_DOMAIN_NAME:-default}"
export OS_PROJECT_NAME="${OS_PROJECT_NAME:-service}"
export OS_USERNAME="${OS_USERNAME:-shipyard}"
export OS_PASSWORD="${OS_PASSWORD:-password}"
export OS_AUTH_URL="${OS_AUTH_URL:-http://keystone.${namespace}:80/v3}"

# Define Color
NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'

# Execute redeploy_server dag
echo -e "Execute redeploy_server Dag...\n"
shipyard create action redeploy_server --param="server-name=${server}"

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

# Retrieve the ID of the 'redeploy_server' action that is currently being executed
echo -e "Retrieving Action ID...\n"
action_id=`shipyard get actions | grep redeploy_server | grep -i Processing | awk '{print $2}'`

if ! [[ ${action_id} ]]; then
    echo "Unable to Retrieve 'redeploy_server' Action ID!"
    exit 1
else
    echo "The Action ID is" ${action_id}
fi

# Initialize 'action_lifecycle' to 'Pending'
action_lifecycle="Pending"

# Polling for 'redeploy_server' action
redeploy_server_counter=1

check_timeout_counter() {

    # Check total elapsed time
    # The default time out is set to 1 hr
    if [[ $redeploy_server_counter -ge $redeploy_server_max_count ]]; then
        echo 'Redeploy server task has timed out.'
        break
    fi
}

while true;
do
    # Get Current State of Action Lifecycle
    describe_action=`shipyard describe ${action_id}`
    action_lifecycle=`echo ${describe_action} | awk '{print $6}'`

    if [[ $action_lifecycle == "Complete" ]]; then
        echo -e '\nServer Successfully Redeployed\n'
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

        # Step counter and check the timeout counter
        ((redeploy_server_counter++))
        check_timeout_counter
    fi
done

# Return exit code so that we can use it to determine the final
# state of the workflow
if [[ $action_lifecycle == "Complete" ]]; then
    exit 0
else
    exit 1
fi
