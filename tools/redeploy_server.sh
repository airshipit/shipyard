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

# We will need to pass the name of the server that we want to redeploy
# when we execute the script. It is mandatory to do so and the script
# will exit with exception if the server name is missing. For instance,
# we can excute the script in the following manner:
#
# $ ./redeploy_server.sh controller01
#
if [[ -z "$1" ]]; then
    echo -e "Please specify the server names as a comma separated string."
    exit 1
fi

# Define Variables
servers=$1

# Source environment variables
source set_env

# Execute shipyard action for redeploy_server
bash execute_shipyard_action.sh 'redeploy_server' ${servers}
