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

# We will need to pass the name of the site/collection as well as the
# path of the directory where the YAMLs are stored when we execute the
# script. It is mandatory to do so and the script will exit with exception
# if these parameters are missing. For instance, we can execute the script
# in the following manner:
#
# $ ./deckhand_load_yaml.sh site1 '/home/ubuntu/site1'
#
if [[ -z "$1" ]]; then
    echo -e "Please specify site/collection name!"
    exit 1
fi

if [[ -z "$2" ]]; then
    echo -e "Please specify the directory where the YAMLs are stored!"
    exit 1
fi

# NOTE: If user is executing the script from outside the cluster, e.g. from
# a remote jump server, then he/she will need to ensure that the DNS server
# is able to resolve the FQDN of the Shipyard and Keystone public URL (both
# will be pointing to the IP of the Ingress Controller). If the DNS resolution
# is not available, the user will need to ensure that the /etc/hosts file is
# properly updated before running the script.

# Define Variables
collection=$1
directory=$2

# Get the path of the directory where the script is located
# Source Base Docker Command
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${DIR} && source shipyard_docker_base_command.sh

# The directory will contain all the .yaml files with Drydock, Promenade,
# Armada, and Divingbell configurations. It will also contain all the
# secrets such as certificates, CAs and passwords.
# We will make use of Shipyard CLI to load all the document as a named
# collection, e.g. "site1" into Deckhand (as a bucket in a revision)
# Note that the name of the collection differs from site to site and is
# specific to that particular deployment
# Note that we will also make use of the '--replace' option so that the
# script can be executed multiple times to replace existing collection
echo -e "Loading YAMLs as named collection..."

${base_docker_command} -v ${directory}:/target ${SHIPYARD_IMAGE} \
create configdocs ${collection} --replace --directory=/target

# Following the creation of a configdocs collection in the Shipyard buffer,
# the configdocs must be committed before Shipyard is able to use them as
# part of an action.
# The other Airship components will be contacted to validate the designs in
# Deckhand when 'commit configdocs' command is executed. Shipyard will
# only mark the revision as committed if the validations are successful
echo -e "Committing Configdocs..."
${base_docker_command} ${SHIPYARD_IMAGE} commit configdocs
