#!/usr/bin/env sh
# In terminal A: ./scripts/failover.sh. In terminal B: docker compose stop backend2.
set -eu
mkdir -p evidence
ab -n 1000 -c 25 -g evidence/failover.tsv http://localhost:8080/api/projects | tee evidence/failover.txt
