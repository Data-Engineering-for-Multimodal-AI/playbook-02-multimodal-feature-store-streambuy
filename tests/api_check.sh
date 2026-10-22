#!/usr/bin/env bash
# Full-stack check of Steps 6-7: start the API against the Docker services, run the
# README's curl calls, restart the API and check that nothing was lost.
# Needs: docker compose up -d (healthy), python download_models.py, and an env with
# requirements.txt installed. Run from the repository root: bash tests/api_check.sh
set -euo pipefail

PY="${PYTHON:-python}"
API="http://localhost:8000"
LOG="${TMPDIR:-/tmp}/streambuy_api.log"

start_api() {
  "$PY" -m uvicorn src.api.main:app --port 8000 >>"$LOG" 2>&1 &
  API_PID=$!
  for _ in $(seq 1 60); do
    curl -sf "$API/docs" >/dev/null && return 0
    kill -0 "$API_PID" 2>/dev/null || { echo "API exited:"; tail -30 "$LOG"; exit 1; }
    sleep 1
  done
  echo "API did not start:"; tail -30 "$LOG"; exit 1
}
stop_api() { kill "$API_PID"; wait "$API_PID" 2>/dev/null || true; }
trap 'kill "${API_PID:-0}" 2>/dev/null || true' EXIT
fail() { echo "FAIL: $*"; exit 1; }

: >"$LOG"
start_api
echo "API started"

# Step 7, as printed: ingest a product
job=$(curl -sf -X POST "$API/products/" -H "Content-Type: application/json" -d '{
    "name": "Blue Yellow Sneakers",
    "category": "footwear",
    "brand": "StreamBuy",
    "price": 89.99,
    "data_paths": {
      "image": "sample_data/product_images/blue_yellow_sneakers.jpg",
      "review": "sample_data/reviews/blue_yellow_sneakers_reviews.txt"
    }
  }')
echo "POST /products/ -> $job"
job_id=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["job_id"])' "$job")
product_id=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["product_id"])' "$job")

for _ in $(seq 1 60); do
  status=$(curl -sf "$API/jobs/$job_id")
  case "$status" in *'"processing"'*) sleep 1 ;; *) break ;; esac
done
echo "GET /jobs/$job_id -> $status"
case "$status" in *'"success"'*) ;; *) fail "job did not succeed" ;; esac

features=$(curl -sf "$API/products/$product_id/features")
n=$("$PY" -c 'import json,sys; print(len(json.loads(sys.argv[1])))' "$features")
echo "GET /products/$product_id/features -> $n results"
[ "$n" = "2" ] || fail "expected 2 results (image, review)"

# Search with a real 512-d vector from the image encoder, in the README's body format
"$PY" - <<'EOF' > "${TMPDIR:-/tmp}/streambuy_query.json"
import json
from src.encoders.factory import EncoderFactory
from src.models.pipeline import Modality
vec = EncoderFactory().create_encoder(Modality.IMAGE).encode("sample_data/product_images/blue_yellow_sneakers.jpg")
print(json.dumps({"query_vector": vec.tolist()}))
EOF
search() {
  curl -sf -X POST "$API/search/image?limit=5" -H "Content-Type: application/json" \
    -d @"${TMPDIR:-/tmp}/streambuy_query.json"
}
hits=$(search)
echo "POST /search/image -> $hits"
case "$hits" in *"\"product_id\":$product_id,"*) ;; *) fail "search did not return the product" ;; esac

code=$(curl -s -o /dev/null -w '%{http_code}' "$API/jobs/999999")
echo "GET /jobs/999999 -> HTTP $code"
[ "$code" = "404" ] || fail "unknown job should be 404"

# Restart the API: vectors and job status must survive
stop_api
start_api
echo "API restarted"
status=$(curl -sf "$API/jobs/$job_id")
echo "GET /jobs/$job_id -> $status"
case "$status" in *'"processed"'*) ;; *) fail "job status lost after restart" ;; esac
hits=$(search)
echo "POST /search/image -> $hits"
case "$hits" in *"\"product_id\":$product_id,"*) ;; *) fail "vectors lost after restart" ;; esac

stop_api
echo "API CHECK PASSED"
