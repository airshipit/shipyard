#!/bin/bash
#
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

set -ex

CMD="shipyard"
PORT=${PORT:-9000}
# Number of uWSGI workers to handle API request
SHIPYARD_API_WORKERS=${SHIPYARD_API_WORKERS:-"4"}
#Threads per worker
SHIPYARD_API_THREADS=${SHIPYARD_API_THREADS:-"1"}

if [ "$1" = 'server' ]; then
    # Start shipyard application
    exec uwsgi \
        --http :${PORT} \
        --paste config:/etc/shipyard/api-paste.ini \
        --enable-threads \
        -L \
        --pyargv "--config-file /etc/shipyard/shipyard.conf" \
        --threads $SHIPYARD_API_THREADS \
        --workers $SHIPYARD_API_WORKERS
else
    # Execute shipyard command
    exec ${CMD} $@
fi
