#!/bin/bash

{{/*
Copyright (c) 2019 AT&T Intellectual Property. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/}}

set -e

if [[ ! -v DB_HOST ]]; then
    echo "environment variable DB_HOST not set"
    exit 1
elif [[ ! -v DB_ADMIN_USER ]]; then
    echo "environment variable DB_ADMIN_USER not set"
    exit 1
elif [[ ! -v PGPASSWORD ]]; then
    echo "environment variable PGPASSWORD not set"
    exit 1
elif [[ ! -v USER_DB_USER ]]; then
    echo "environment variable USER_DB_USER not set"
    exit 1
elif [[ ! -v DB_PORT ]]; then
    echo "environment variable USER_DB_USER not set"
    exit 1
elif [[ ! -v USER_DB_NAME ]]; then
    echo "environment variable USER_DB_NAME not set"
    exit 1
else
    echo "Got DB connection info"
fi

# Grant permissions to shipyard user to the airflow dataabase tables
# This will allow shipyard user to query airflow database
/usr/bin/psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_ADMIN_USER} -d ${AIRFLOW_DB_NAME} \
--command="GRANT select, insert, update, delete on all tables in schema public to $USER_DB_USER;"
