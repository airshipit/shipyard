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

set -e

# User can run the script as they would execute the Shipyard CLI.
# For instance, to run the 'shipyard get actions' command, user can execute
# the following command after setting up the required environment variables:
#
# $ ./tools/shipyard.sh get actions
#

# NOTE: If user is executing the script from outside the cluster, e.g. from
# a remote jump server, then he/she will need to ensure that the DNS server
# is able to resolve the FQDN of the Shipyard and Keystone public URL (both
# will be pointing to the IP of the Ingress Controller). If the DNS resolution
# is not available, the user will need to ensure that the /etc/hosts file is
# properly updated before running the script.

# Commands requiring files as input utilize the pwd mounted into the container
# as the /target directory, e.g.:
#
# $ ./tools/shipyard.sh create configdocs design --filename=/target/afile.yaml

# Get the path of the directory where the script is located
# Source Base Docker Command
SHIPYARD_HOSTPATH=${SHIPYARD_HOSTPATH:-"/target"}
NAMESPACE="${NAMESPACE:-ucp}"
DISTRO="${DISTRO:-ubuntu_jammy}"
SHIPYARD_IMAGE="${SHIPYARD_IMAGE:-quay.io/airshipit/shipyard:master-${DISTRO}}"
# set default value for OS_PASSWORD if it's not set
# this doesn't actually get exported to environment
# unless the script is sourced
OS_SHIPYARD_PASSWORD=${OS_SHIPYARD_PASSWORD:-${OS_PASSWORD}}
export OS_PASSWORD=${OS_SHIPYARD_PASSWORD:-password}

# Define Base Docker Command
base_docker_command=$(cat << EndOfCommand
sudo -E docker run -t --rm --net=host
-e http_proxy=${HTTP_PROXY}
-e https_proxy=${HTTPS_PROXY}
-e no_proxy=${NO_PROXY:-127.0.0.1,localhost,.svc.cluster.local}
-e OS_AUTH_URL=${OS_AUTH_URL:-http://keystone.${NAMESPACE}.svc.cluster.local:80/v3}
-e OS_USERNAME=${OS_USERNAME:-shipyard}
-e OS_USER_DOMAIN_NAME=${OS_USER_DOMAIN_NAME:-default}
-e OS_PASSWORD
-e OS_PROJECT_DOMAIN_NAME=${OS_PROJECT_DOMAIN_NAME:-default}
-e OS_PROJECT_NAME=${OS_PROJECT_NAME:-service}
EndOfCommand
)

# Execute Shipyard CLI
${base_docker_command} -v "$(pwd)":"${SHIPYARD_HOSTPATH}" "${SHIPYARD_IMAGE}" $@
