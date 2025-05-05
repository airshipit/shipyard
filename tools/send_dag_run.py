#!/usr/bin/env python3

import requests
import pendulum
import json
import uuid
import base64

def generate_base32_id():
    # Generate a UUID
    unique_id = uuid.uuid4()
    # Encode the UUID as Base32 and remove padding
    base32_id = base64.b32encode(unique_id.bytes).decode('utf-8').strip('=')
    return base32_id

# Generate a UUID
generated_uuid = uuid.uuid4

# Convert UUID to string before serializing
data = {"id": str(generated_uuid)}

# Serialize to JSON
json_uuid = json.dumps(data)

# Step 1: Get the authentication token
auth_url = "http://localhost:8080/auth/token"
response = requests.get(auth_url)
response.raise_for_status()
token = response.json().get("access_token")

# Step 2: Generate the logical_date
logical_date = pendulum.now("UTC").to_iso8601_string()

# Step 3: Define the payload
payload = {
    "dag_run_id": generate_base32_id(),
    "logical_date": logical_date,
    "conf": {
        "action": {
            "name": "update_software",
            "parameters": {},
            "id": generate_base32_id(),
            "user": "admin",
            "timestamp": logical_date,
            "context_marker": json_uuid,
            "dag_id": "update_software",
            "committed_rev_id": 1,
            "allow_intermediate_commits": True
        }
    }
}

# Step 4: Send the POST request
dag_run_url = "http://localhost:8080/api/v2/dags/update_software/dagRuns"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(dag_run_url, headers=headers, json=payload)
response.raise_for_status()

# Step 5: Print the response
print(json.dumps(response.json(), indent=2))
