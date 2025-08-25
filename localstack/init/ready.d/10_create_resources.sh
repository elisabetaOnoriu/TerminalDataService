#!/usr/bin/env bash
set -euo pipefail

# Create SQS queue for Terminal Service
awslocal sqs create-queue --queue-name terminal-events-queue

echo "[localstack] SQS queue 'terminal-events-queue' created."
