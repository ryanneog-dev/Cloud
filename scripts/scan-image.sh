#!/usr/bin/env sh
set -eu
mkdir -p evidence
docker build -f Dockerfile.baseline -t project-tracker:baseline .
trivy image --severity HIGH,CRITICAL --format table project-tracker:baseline | tee evidence/trivy-before.txt
docker build -t project-tracker:hardened .
trivy image --severity HIGH,CRITICAL --format table project-tracker:hardened | tee evidence/trivy-after.txt
