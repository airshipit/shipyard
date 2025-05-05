#!/bin/bash
set -e

# URL to check
URL="http://localhost:8080/auth/token"

# Timeout in seconds
TIMEOUT=300
INTERVAL=5
ELAPSED=0

echo "Waiting for API server to be reachable at $URL..."

while ! curl -i --fail "$URL"; do
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "Timeout reached! API server is not reachable at $URL."
    exit 1
  fi

  echo "API server not reachable yet. Retrying in $INTERVAL seconds..."
  sleep "$INTERVAL"
  ELAPSED=$((ELAPSED + INTERVAL))
done

echo "API server is now reachable at $URL."
