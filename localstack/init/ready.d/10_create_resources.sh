#!/usr/bin/env bash
set -euo pipefail

awslocal sqs create-queue --queue-name terminal-events-queue

echo "[localstack] SQS queue 'terminal-events-queue' created."
