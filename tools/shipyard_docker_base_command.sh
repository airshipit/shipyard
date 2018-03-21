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

# Define Variables
#
# NOTE: User will need to set up the required environment variables
# before executing this script if they differ from the default values.
#
NAMESPACE="${NAMESPACE:-ucp}"
SHIPYARD_IMAGE="${SHIPYARD_IMAGE:-quay.io/attcomdev/shipyard:latest}"

# Define Base Docker Command
base_docker_command=$(cat << EndOfCommand
sudo docker run -t --rm --net=host
-e http_proxy=${HTTP_PROXY}
-e https_proxy=${HTTPS_PROXY}
-e OS_AUTH_URL=${OS_AUTH_URL:-http://keystone.${NAMESPACE}.svc.cluster.local:80/v3}
-e OS_USERNAME=${OS_USERNAME:-shipyard}
-e OS_USER_DOMAIN_NAME=${OS_USER_DOMAIN_NAME:-default}
-e OS_PASSWORD=${OS_PASSWORD:-password}
-e OS_PROJECT_DOMAIN_NAME=${OS_PROJECT_DOMAIN_NAME:-default}
-e OS_PROJECT_NAME=${OS_PROJECT_NAME:-service}
EndOfCommand
)
