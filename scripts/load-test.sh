#!/usr/bin/env bash
# Generates API traffic so Grafana panels populate and the HPA has CPU to react to.
#   URL=http://medislot.local scripts/load-test.sh            # through the Ingress
#   URL=http://<elb-hostname> REQUESTS=20000 CONCURRENCY=50 scripts/load-test.sh
set -euo pipefail
URL="${URL:-http://medislot.local}"
REQUESTS="${REQUESTS:-5000}"
CONCURRENCY="${CONCURRENCY:-25}"

echo "Sending $REQUESTS requests to $URL with concurrency $CONCURRENCY"
echo "Watch:  kubectl get hpa -n medislot -w"

paths=(/api/appointments /api/appointments/stats /api/doctors /api/doctors/1 /api/appointments/999999)
for ((i = 0; i < REQUESTS; i++)); do
  echo "$URL${paths[i % ${#paths[@]}]}"
done | xargs -P "$CONCURRENCY" -n 1 curl -s -o /dev/null

echo "Load test completed"
