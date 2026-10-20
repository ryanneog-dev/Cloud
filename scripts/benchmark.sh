#!/usr/bin/env sh
# Usage: ./scripts/benchmark.sh http://localhost:8080/api/projects 1|3
# Requires ApacheBench. Run each case after `docker compose up -d` with the selected backend count.
set -eu
url="${1:?URL required}"; instances="${2:?instance count required}"
mkdir -p evidence
ab -n 1000 -c 25 -g "evidence/ab-${instances}-instances.tsv" "$url" | tee "evidence/ab-${instances}-instances.txt"
