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

set -x

# User can run the script like how they would execute the Shipyard CLI.
# For instance, to run the 'shipyard get actions' command, user can execute
# the following command after setting up the required environment variables:
#
# $ ./tools/run_shipyard.sh get actions
#

# NOTE: User can retrieve the IP of the ingress_controller_ip by executing
# the following command:
#
# ingress_controller_ip=`sudo kubectl get pods -n ucp -o wide | grep -v ingress-error-pages | grep -m 1 ingress | awk '{print $6}'`
#

# NOTE: User should update /etc/hosts with the IP of the ingress
# controller if DNS resolution of the Keystone and Shipyard URLs
# is not available. User can execute the following command to update
# the /etc/hosts file:
#
# cat << EOF | sudo tee -a /etc/hosts
#
# $ingress_controller_ip keystone.ucp
# $ingress_controller_ip shipyard-api.ucp.svc.cluster.local
# EOF
#

# NOTE: User will need to set up the necessary environment variables
# before executing this script. For instance, user can set up the
# environment with the following default values:
#
# export SHIPYARD_IMAGE='quay.io/attcomdev/shipyard:latest'
# export OS_AUTH_URL="http://keystone.ucp:80/v3"
# export OS_IDENTITY_API_VERSION=3
# export OS_USERNAME="shipyard"
# export OS_USER_DOMAIN_NAME="default"
# export OS_PASSWORD="password"
# export OS_PROJECT_DOMAIN_NAME="default"
# export OS_PROJECT_NAME="service"
#
# Define OpenStack Environment Variables
OS_AUTH_URL=`env | grep OS_AUTH_URL`
OS_IDENTITY_API_VERSION=`env | grep OS_IDENTITY_API_VERSION`
OS_USERNAME=`env | grep OS_USERNAME`
OS_USER_DOMAIN_NAME=`env | grep OS_USER_DOMAIN_NAME`
OS_PASSWORD=`env | grep OS_PASSWORD`
OS_PROJECT_DOMAIN_NAME=`env | grep OS_PROJECT_DOMAIN_NAME`
OS_PROJECT_NAME=`env | grep OS_PROJECT_NAME`

# Define shipyard image variable
# NOTE: We only want the location of the image. Hence we will need
# to stip off 'SHIPYARD_IMAGE=' from SHIPYARD_IMAGE_ENV_VARIABLE
SHIPYARD_IMAGE_ENV_VARIABLE=`env | grep SHIPYARD_IMAGE`
SHIPYARD_IMAGE="${SHIPYARD_IMAGE_ENV_VARIABLE#*=}"

# Define Base Docker Command
# NOTE: We will mount the current directory so that any directories
# would be relative to that
# NOTE: We will map the host directory to '/home/shipyard/host' on
# the Shipyard docker container
read -r -d '' base_docker_command << EOM
sudo docker run
-e ${OS_AUTH_URL}
-e ${OS_IDENTITY_API_VERSION}
-e ${OS_USERNAME}
-e ${OS_USER_DOMAIN_NAME}
-e ${OS_PASSWORD}
-e ${OS_PROJECT_DOMAIN_NAME}
-e ${OS_PROJECT_NAME}
--rm --net=host
-v $(pwd):/home/shipyard/host/
EOM

# Execute Shipyard CLI
# We will pass all arguments in and the Shipyard CLI will perform
# the actual validation and execution. Exceptions will also be
# handled by the Shipyard CLI as this is meant to be a thin wrapper
# script
${base_docker_command} ${SHIPYARD_IMAGE} $@
