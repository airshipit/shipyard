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

# Define Variables
namespace="ucp"
shipyard_username="shipyard"
shipyard_password="password"
keystone_ip=`kubectl get pods -n ${namespace} -o wide | grep keystone | awk '{print $6}'`
host="localhost"
port=31901

#Define Color
NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'

# Retrieve Keystone Token
echo -e "Retrieving Keystone Token...\n"
TOKEN=`sudo docker run -t \
       -e "OS_AUTH_URL=http://${keystone_ip}:80/v3" \
       -e "OS_PROJECT_NAME=service" \
       -e "OS_USER_DOMAIN_NAME=Default" \
       -e "OS_USERNAME=${shipyard_username}" \
       -e "OS_PASSWORD=${shipyard_password}" \
       -e "OS_REGION_NAME=RegionOne" \
       -e "OS_IDENTITY_API_VERSION=3" \
       --net=host \
       docker.io/kolla/ubuntu-source-keystone:3.0.3 \
       openstack token issue | grep -w 'id' | awk '{print $4}'`

# Execute deploy_site
echo -e "Execute deploy_site Dag...\n"

# Save output to tmp file
curl -sS -D - -d '{"name":"deploy_site"}' \
              -X POST ${host}:${port}/api/v1.0/actions \
              -H "X-Auth-Token:${TOKEN}" \
              -H "content-type:application/json" > /tmp/deploy_site_response.json

# The response will not be in proper json format, we will extract the required
# json output by deleteing everything before we encounter the first '{'
sed -i '/{/,$!d' /tmp/deploy_site_response.json

echo -e "Retrieving Action ID...\n"
action_id=`cat /tmp/deploy_site_response.json | jq -r '.id'`

echo "The Action ID is" ${action_id}
echo

# The status or lifecycle phase of an action can be
#
# 1) Pending - The action is scheduled or preparing for execution.
# 2) Processing - The action is underway.
# 3) Complete - The action has completed successfully.
# 4) Failed - The action has encountered an error, and has failed.
# 5) Paused - The action has been paused by a user.
#
# Initialize 'action_lifecycle' to 'Pending'
action_lifecycle="Pending"

while true;
do
    if [[ $action_lifecycle == "Complete" ]] || [[ $action_lifecycle == "Failed" ]] || [[ $action_lifecycle == "Paused" ]]; then
        # Print final results
        echo -e '\nFinal State of Deployment\n'
        cat /tmp/get_action_status.json | jq
        break
    else
        # Get Current State of Action Lifecycle
        # Save output to tmp file
        curl -sS -D - -X GET ${host}:${port}/api/v1.0/actions/${action_id} \
                      -H "X-Auth-Token:${TOKEN}" \
                      -H "content-type:application/json" > /tmp/get_action_status.json

        # The response will not be in proper json format, we will extract the required
        # json output by deleteing everything before we encounter the first '{'
        sed -i '/{/,$!d' /tmp/get_action_status.json

        action_lifecycle=`cat /tmp/get_action_status.json | jq -r '.action_lifecycle'`

        # Sleep for 10 seconds between each iteration
        echo -e "Back Off for 10 seconds...\n"
        sleep 10

        # Check Dag state
        if [[ $action_lifecycle == "Failed" ]] || [[ $action_lifecycle == "Paused" ]]; then
            echo -e "Dag Execution is in" ${RED}$action_lifecycle${NC} "state\n"
        else
            echo -e "Dag Execution is in" ${GREEN}$action_lifecycle${NC} "state\n"
        fi
    fi
done

# Delete the temporary files
rm /tmp/deploy_site_response.json
rm /tmp/get_action_status.json

# Return exit code so that we can use it to determine the final
# state of the workflow
if [[ $action_lifecycle == "Complete" ]]; then
    exit 0
else
    exit 1
fi
