#!/bin/bash
# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
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

# We will need to pass the name of the helm release to test. It is mandatory.
# cleanup may also be passed. By default, test pods will be cleaned up.
# we can execute the script in the following manner:
#
# $ ./test_release.sh helm_release
#
if [[ -z "$1" ]]; then
    echo -e "Please specify the Helm release name."
    exit 1
fi

# Define Variables
helm_release=$1
cleanup=${2:-true}

# Source environment variables
source set_env

# Execute shipyard action for test_site
bash execute_shipyard_action.sh 'test_site' --param="release=${helm_release}" --param="cleanup=${cleanup}"
