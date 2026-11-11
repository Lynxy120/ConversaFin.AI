#!/usr/bin/env bash
cd "$(dirname "$0")/.."; sed -i 's/\r$//' .env; set -a; source .env; set +a
f=0; chk(){ [[ "$3" == "$2" ]] && echo "[PASS] $1" || { echo "[FAIL] $1 (got $3, want $2)"; f=1; }; }
code(){ curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$@"; }
jget(){ python -c "import sys,json;print(json.load(sys.stdin).get('$1'))"; }
TG="https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN"; GB="https://generativelanguage.googleapis.com/v1beta"
S=(-H "apikey: $SUPABASE_KEY" -H "Authorization: Bearer $SUPABASE_KEY")
BASE="${BASE_URL:-http://localhost:8000}"

tg(){ chk "telegram getMe" 200 "$(code $TG/getMe)"; curl -s $TG/getMe | python -c "import sys,json;r=json.load(sys.stdin)['result'];print('  bot: @'+r['username'])"; }
tgwh(){ curl -s $TG/getWebhookInfo | python -m json.tool; }
supabase(){ for t in "$@"; do chk "supabase $t" 200 "$(code "${S[@]}" "$SUPABASE_URL/rest/v1/$t?select=*&limit=1")"; done; }
supabase_rw(){ ID=$(curl -s -X POST "${S[@]}" -H 'Content-Type: application/json' -H 'Prefer: return=representation' \
  -d '{"sku":"PROBE-'$$'","name":"probe","price":1}' "$SUPABASE_URL/rest/v1/products" | python -c "import sys,json;print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
  chk "supabase insert" yes "$([[ -n "$ID" ]] && echo yes || echo no)"
  chk "supabase delete" 204 "$(code -X DELETE "${S[@]}" "$SUPABASE_URL/rest/v1/products?id=eq.$ID")"; }
midtrans(){ chk "midtrans server key (404 body = key valid)" 404 "$(curl -s -u "$MIDTRANS_SERVER_KEY:" https://api.sandbox.midtrans.com/v2/CF-KEYCHECK/status | jget status_code)"; }
midtrans_qris(){ chk "midtrans QRIS charge" 201 "$(curl -s -X POST -u "$MIDTRANS_SERVER_KEY:" -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"payment_type":"qris","transaction_details":{"order_id":"CF-V-'$(date +%s)'","gross_amount":10000},"qris":{"acquirer":"gopay"}}' https://api.sandbox.midtrans.com/v2/charge | jget status_code)"; }
gemini(){ chk "gemini model $GEMINI_MODEL exists" 200 "$(code -H "x-goog-api-key: $GEMINI_API_KEY" $GB/models/$GEMINI_MODEL)"
  chk "gemini generateContent" 200 "$(code -X POST -H "x-goog-api-key: $GEMINI_API_KEY" -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Reply OK"}]}]}' $GB/models/$GEMINI_MODEL:generateContent)"; }
gemini_models(){ curl -s -H "x-goog-api-key: $GEMINI_API_KEY" "$GB/models?pageSize=200" | python -c "import sys,json;[print(m['name']) for m in json.load(sys.stdin)['models'] if 'flash' in m['name']]"; }
backend(){ chk "backend GET /" 200 "$(code $BASE/)"; }
render(){ BASE=https://conversafin-ai.onrender.com; backend; }
tg_route(){ chk "telegram webhook route + secret enforced (wrong secret = 403)" 403 "$(code -X POST $BASE/telegram/webhook -H 'X-Telegram-Bot-Api-Secret-Token: wrong' -H 'Content-Type: application/json' -d '{}')"; }
"$@"; exit $f