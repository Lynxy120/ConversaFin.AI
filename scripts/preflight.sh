#!/usr/bin/env bash
# Run: bash scripts/preflight.sh   (backend must be running on :8000)
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

GRAPH="https://graph.facebook.com/${WA_GRAPH_VERSION:-v23.0}"
BACKEND="${BACKEND_URL:-http://localhost:8000}"
pass=0; fail=0

chk() { # name expected actual
  if [[ "$3" == "$2" ]]; then echo "[PASS] $1 (HTTP $3)"; pass=$((pass+1))
  else echo "[FAIL] $1 (HTTP $3, expected $2)"; fail=$((fail+1)); fi
}
code() { curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$@"; }

echo "== Backend (W2)"
chk "GET /"                    200 "$(code "$BACKEND/")"
chk "GET /webhook valid token" 200 "$(code "$BACKEND/webhook?hub.mode=subscribe&hub.verify_token=$WA_VERIFY_TOKEN&hub.challenge=123")"
chk "GET /webhook bad token"   403 "$(code "$BACKEND/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=123")"

echo "== WhatsApp Cloud API"
WA=(-H "Authorization: Bearer $WA_ACCESS_TOKEN")
chk "phone number object"  200 "$(code "${WA[@]}" "$GRAPH/$WA_PHONE_NUMBER_ID?fields=display_phone_number,verified_name,quality_rating")"
chk "WABA subscribed_apps" 200 "$(code "${WA[@]}" "$GRAPH/$WA_WABA_ID/subscribed_apps")"
chk "commerce settings"    200 "$(code "${WA[@]}" "$GRAPH/$WA_PHONE_NUMBER_ID/whatsapp_commerce_settings")"

echo "== Supabase DB + Storage"
SB=(-H "apikey: $SUPABASE_KEY" -H "Authorization: Bearer $SUPABASE_KEY")
for t in products orders financial_records; do
  chk "table $t" 200 "$(code "${SB[@]}" "$SUPABASE_URL/rest/v1/$t?select=id&limit=1")"
done
chk "storage bucket list" 200 "$(code "${SB[@]}" "$SUPABASE_URL/storage/v1/bucket")"

echo "== Midtrans Sandbox"
chk "Snap create transaction" 201 "$(code -X POST -u "$MIDTRANS_SERVER_KEY:" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d "{\"transaction_details\":{\"order_id\":\"W3-PREFLIGHT-$(date +%s)\",\"gross_amount\":10000}}" \
  https://app.sandbox.midtrans.com/snap/v1/transactions)"

echo "== Gemini"
chk "generateContent $GEMINI_MODEL" 200 "$(code -X POST \
  -H "x-goog-api-key: $GEMINI_API_KEY" -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Reply OK"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/$GEMINI_MODEL:generateContent")"

echo "== W2 automated suite"
python scripts/test_w2_webhook.py || fail=$((fail+1))

echo; echo "preflight: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
