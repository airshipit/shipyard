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

# We will need to pass the name of the site/collection as well as the
# path of the directory where the YAMLs are stored when we execute the
# script. It is mandatory to do so and the script will exit with exception
# if these parameters are missing. For instance, we can excute the script
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

# Define Variables
collection=$1
directory=$2
namespace="ucp"

# Initialize Variables with Default Values
OS_USER_DOMAIN_NAME="default"
OS_PROJECT_DOMAIN_NAME="default"
OS_PROJECT_NAME="service"
OS_USERNAME="shipyard"
OS_PASSWORD="password"
OS_AUTH_URL="http://keystone.${namespace}:80/v3"

# Determine IP address of Ingress Controller
ingress_controller_ip=`sudo kubectl get pods -n ${namespace} -o wide | grep -v ingress-error-pages | grep -m 1 ingress | awk '{print $6}'`

# Update /etc/hosts with the IP of the ingress controller
# Note that these values would need to be set in the case
# where DNS resolution of the Keystone and Shipyard URLs
# is not available. We can skip this step if DNS is in place.
cat << EOF | sudo tee -a /etc/hosts

$ingress_controller_ip keystone.${namespace}
$ingress_controller_ip shipyard-api.${namespace}.svc.cluster.local
EOF

# Set up Genesis host with the Shipyard Client
# This will allow us to use the Shipyard CLI
git clone --depth=1 https://github.com/att-comdev/shipyard.git
sudo apt install python3-pip -y
sudo pip3 install --upgrade pip
cd shipyard && sudo pip3 install -r requirements.txt
sudo python3 setup.py install

# Export Environment Variables
export OS_USER_DOMAIN_NAME=${OS_USER_DOMAIN_NAME}
export OS_PROJECT_DOMAIN_NAME=${OS_PROJECT_DOMAIN_NAME}
export OS_PROJECT_NAME=${OS_PROJECT_NAME}
export OS_USERNAME=${OS_USERNAME}
export OS_PASSWORD=${OS_PASSWORD}
export OS_AUTH_URL=${OS_AUTH_URL}

# The directory will contain all the .yaml files with Drydock, Promenade,
# Armada, and Divingbell configurations. It will also contain all the
# secrets such as certificates, CAs and passwords.
# We will make use of Shipyard CLI to load all the document as a named
# collection, e.g. "site1" into Deckhand (as a bucket in a revision)
# Note that the name of the collection differs from site to site and is
# specific to that particular deployment
echo -e "Loading YAMLs as named collection..."
shipyard create configdocs ${collection} --directory=${directory}

# Following the creation of a configdocs collection in the Shipyard buffer,
# the configdocs must be committed before Shipyard is able to use them as
# part of an action.
# The other UCP components will be contacted to validate the designs in
# Deckhand when 'commit configdocs' command is executed. Shipyard will
# only mark the revision as committed if the validations are successful
echo -e "Committing Configdocs..."
shipyard commit configdocs

# Exit the script
exit 0
