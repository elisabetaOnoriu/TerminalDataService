#!/usr/bin/env bash
set -euo pipefail

# awslocal resources create-queue --queue-name terminal-events-queue

awslocal sqs create-queue --queue-name terminal-messages

echo "[localstack] SQS queue 'terminal--messs' created."
