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
#
set -x

IMAGE=$1
USE_PROXY=${USE_PROXY:-false}

# Collect necessary files and run shipyard image in docker
mkdir -p build/.tmprun/etc
cp $PWD/etc/shipyard/api-paste.ini build/.tmprun/etc
cp $PWD/tools/resources/shipyard.conf build/.tmprun/etc
docker run \
    -v $PWD/build/.tmprun/etc:/etc/shipyard \
    -p 9000:9000 \
    --name shipyard_test ${IMAGE} \
    &

sleep 5

RESULT="$(curl -i 'http://127.0.0.1:9000/versions' --noproxy '*' | tr '\r' '\n' | head -1)"

if [ "${USE_PROXY}" == "true" ]; then
  CLI_RESULT="$(docker run -t --rm --net=host --env HTTP_PROXY="${PROXY}" --env HTTPS_PROXY="${PROXY}" ${IMAGE} help | tr '\r' '\n' | head -1)"
else
  CLI_RESULT="$(docker run -t --rm --net=host ${IMAGE} help | tr '\r' '\n' | head -1)"
fi

docker stop shipyard_test
docker rm shipyard_test
rm -r build/.tmprun
GOOD="HTTP/1.1 200 OK"
CLI_GOOD="THE SHIPYARD COMMAND"
if [[ ${RESULT} == ${GOOD} && ${CLI_RESULT} == ${CLI_GOOD} ]]; then
    exit 0
else
    exit 1
fi
