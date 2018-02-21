#!/bin/bash
#
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

while true; do

    # Delete logs that are more than 30 days old in the directories
    # under the Airflow log path
    # Delete empty directories under the Airflow log path
    find ${LOGROTATE_PATH} \( -type f -name '*.log' -mtime +${DAYS_BEFORE_LOG_DELETION} -o -type d -empty \) -print -delete

    # Sleep for 1 hr between each wait loop
    sleep 3600

done
