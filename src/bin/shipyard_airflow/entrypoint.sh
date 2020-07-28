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

set -e
if [ "$1" = 'server' ]; then
    set -x
    PORT=${PORT:-9000}
    HTTP_TIMEOUT=${HTTP_TIMEOUT:-600}
    # Number of uWSGI workers to handle API request
    SHIPYARD_API_WORKERS=${SHIPYARD_API_WORKERS:-"16"}
    #Threads per worker
    SHIPYARD_API_THREADS=${SHIPYARD_API_THREADS:-"1"}
    # use uwsgi cheaper-busyness plugin for dynamic worker scaling
    SHIPYARD_API_CHEAPER_ALGO=${SHIPYARD_API_CHEAPER_ALGO:-"busyness"}
    # Minimum number of workers allowed
    SHIPYARD_API_CHEAPER=${SHIPYARD_API_CHEAPER:-"4"}
    # Number of workers created at startup
    SHIPYARD_API_CHEAPER_INITIAL=${SHIPYARD_API_CHEAPER_INITIAL:-"8"}
    # How many workers to spawn each time
    SHIPYARD_API_CHEAPER_STEP=${SHIPYARD_API_CHEAPER_STEP:-"4"}
    # Length of a busyness cycle in seconds
    SHIPYARD_API_CHEAPER_OVERLOAD=${SHIPYARD_API_CHEAPER_OVERLOAD:-"1"}
    # How many cycles to wait before killing workers due to low load
    SHIPYARD_API_CHEAPER_BUSYNESS_MULTIPLIER=${SHIPYARD_API_CHEAPER_BUSYNESS_MULTIPLIER:-"60"}
    # Below this threshold, kill workers (if stable for multiplier cycles)
    SHIPYARD_API_CHEAPER_BUSYNESS_MIN=${SHIPYARD_API_CHEAPER_BUSYNESS_MIN:-"20"}
    # Above this threshold, spawn new workers
    SHIPYARD_API_CHEAPER_BUSYNESS_MAX=${SHIPYARD_API_CHEAPER_BUSYNESS_MAX:-"75"}
    # Spawn emergency workers if more than this many requests are waiting in the queue
    SHIPYARD_API_CHEAPER_BUSYNESS_BACKLOG_ALERT=${SHIPYARD_API_CHEAPER_BUSYNESS_BACKLOG_ALERT:-"40"}
    # How many emergegency workers to create if there are too many requests in the queue
    SHIPYARD_API_CHEAPER_BUSYNESS_BACKLOG_STEP=${SHIPYARD_API_CHEAPER_BUSYNESS_BACKLOG_STEP:-"1"}
    # Start shipyard application
    # for more info about these default overrides please read
    # https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
    exec uwsgi \
        --http :${PORT} \
        --paste config:/etc/shipyard/api-paste.ini \
        --enable-threads \
        -L \
        --pyargv "--config-file /etc/shipyard/shipyard.conf" \
        --threads ${SHIPYARD_API_THREADS} \
        --workers ${SHIPYARD_API_WORKERS} \
        --http-timeout ${HTTP_TIMEOUT} \
        --strict \
        --master \
        --vacuum \
        --single-interpreter \
        --die-on-term \
        --need-app \
        --cheaper-algo ${SHIPYARD_API_CHEAPER_ALGO} \
        --cheaper ${SHIPYARD_API_CHEAPER} \
        --cheaper-initial ${SHIPYARD_API_CHEAPER_INITIAL} \
        --cheaper-step ${SHIPYARD_API_CHEAPER_STEP} \
        --cheaper-overload ${SHIPYARD_API_CHEAPER_OVERLOAD} \
        --cheaper-busyness-multiplier ${SHIPYARD_API_CHEAPER_BUSYNESS_MULTIPLIER} \
        --cheaper-busyness-min ${SHIPYARD_API_CHEAPER_BUSYNESS_MIN} \
        --cheaper-busyness-max ${SHIPYARD_API_CHEAPER_BUSYNESS_MAX} \
        --cheaper-busyness-backlog-alert ${SHIPYARD_API_CHEAPER_BUSYNESS_BACKLOG_ALERT} \
        --cheaper-busyness-backlog-step ${SHIPYARD_API_CHEAPER_BUSYNESS_BACKLOG_STEP}
else
    CMD="shipyard"
    # Execute shipyard command
    exec ${CMD} $@
fi
