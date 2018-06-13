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

# User can run the script like how they would execute the Shipyard CLI.
# For instance, to run the 'shipyard get actions' command, user can execute
# the following command after setting up the required environment variables:
#
# $ ./tools/run_shipyard.sh get actions
#

# NOTE: If user is executing the script from outside the cluster, e.g. from
# a remote jump server, then he/she will need to ensure that the DNS server
# is able to resolve the FQDN of the Shipyard and Keystone public URL (both
# will be pointing to the IP of the Ingress Controller). If the DNS resolution
# is not available, the user will need to ensure that the /etc/hosts file is
# properly updated before running the script.

# Get the path of the directory where the script is located
# Source Base Docker Command
DIR="$(realpath $(dirname "${BASH_SOURCE}"))"
source "${DIR}/shipyard_docker_base_command.sh"

# Execute Shipyard CLI
#
# NOTE: We will mount the current directory so that any directories
# would be relative to that
#
# NOTE: We will map the host directory to '/home/shipyard/host' on
# the Shipyard docker container
#
# We will pass all arguments in and the Shipyard CLI will perform
# the actual validation and execution. Exceptions will also be
# handled by the Shipyard CLI as this is meant to be a thin wrapper
# script
${base_docker_command} -v $(pwd):/home/shipyard/host ${SHIPYARD_IMAGE} $@
