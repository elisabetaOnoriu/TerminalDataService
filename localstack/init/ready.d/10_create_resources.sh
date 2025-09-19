#!/usr/bin/env bash
set -euo pipefail

awslocal resources create-queue --queue-name terminal-events-queue

echo "[localstack] SQS queue 'terminal-events-queue' created."
