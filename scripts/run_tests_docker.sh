#!/bin/bash
# Script para ejecutar tests dentro de Docker (Python 3.12)
# Uso: ./scripts/run_tests_docker.sh

set -e

IMAGE_NAME="local-rag:test"
CONTAINER_NAME="local-rag-test"

echo "=== Building Docker image ==="
docker build -t "$IMAGE_NAME" .

echo "=== Running tests in container ==="
docker run --rm \
    -v "$(pwd)/coverage.xml:/app/coverage.xml" \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME" \
    pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing

echo "=== Tests completed ==="