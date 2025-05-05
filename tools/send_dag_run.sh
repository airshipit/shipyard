#!/bin/bash

set -ex

# Get the authentication token
TOKEN=$(curl -X "GET" "http://localhost:8080/auth/token" 2>/dev/null | jq -r .access_token)

logical_date=$(python3 -c "import pendulum; print(pendulum.now('UTC'))")

# Define the payload with the provided logical_date
PAYLOAD=$(cat <<EOF
{
  "dag_run_id": "01JTP12Q7X6MW2QYR3GSP31CX5",
  "logical_date": "${logical_date}",
  "conf": {
    "action": {
      "name": "update_software",
      "parameters": {},
      "id": "01JTP12Q7X6MW2QYR3GSP31CX5",
      "user": "admin",
      "timestamp": "2025-05-07T18:45:41.246269",
      "context_marker": "99cd05f9-e529-49bf-9a9c-f68647715286",
      "dag_id": "update_software",
      "committed_rev_id": 1,
      "allow_intermediate_commits": true
    }
  }
}
EOF
)

# Send the POST request
curl -X POST "http://localhost:8080/api/v2/dags/update_software/dagRuns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  2>/dev/null | jq
