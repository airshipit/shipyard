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

IMAGE_PREFIX=$1
AIRFLOW_IMAGE_NAME=$2
IMAGE_TAG=$3

TEST_RESP="$(docker run \
    -p 8080:8080 \
    --name airflow_test ${IMAGE_PREFIX}/${AIRFLOW_IMAGE_NAME}:${IMAGE_TAG} \
    quicktest)"

docker stop airflow_test
docker rm airflow_test

if [[ ${TEST_RESP:(-7)} == "success" ]]; then
    exit 0
else
    exit 1
fi
