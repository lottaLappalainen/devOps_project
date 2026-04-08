#!/bin/sh
set -e

echo "Starting temporary API service..."
docker run -d --name test_api -p 8199:8199 api_v1:latest
sleep 5

echo "Checking API /status..."
curl -sSf http://localhost:8199/status

echo "Test PASSED"

docker stop test_api
docker rm test_api
