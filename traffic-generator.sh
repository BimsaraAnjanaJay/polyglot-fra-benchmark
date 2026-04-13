#!/bin/sh

GATEWAY=${GATEWAY_URL:-"http://localhost:8000"}

echo "Starting benchmark experiment on $GATEWAY..."
curl -s -X POST "$GATEWAY/run-experiment" \
  -H "Content-Type: application/json" \
  -d '{"rounds":5,"sleep_between_rounds_ms":200}'

echo "Waiting for traffic to complete..."
sleep 10
echo "Traffic generation finished."
