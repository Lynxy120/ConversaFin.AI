#!/usr/bin/env bash
cd "$(dirname "$0")/.."; sed -i 's/\r$//' .env; set -a; source .env; set +a
M="${GEMINI_MODEL:-gemini-3.8-flash}"; GB="https://generativelanguage.googleapis.com/v1beta"
GH=(-H "x-goog-api-key: $GEMINI_API_KEY"); S=(-H "apikey: $SUPABASE_KEY" -H "Authorization: Bearer $SUPABASE_KEY"); f=0
c(){ [[ "$3" == "$2" ]] && echo "[PASS] $1" || { echo "[FAIL] $1 (got $3, want $2)"; f=1; }; }
h(){ curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$@"; }

c "gemini key valid"            200 "$(h "${GH[@]}" "$GB/models?pageSize=1")"
c "gemini model $M exists"      200 "$(h "${GH[@]}" "$GB/models/$M")"
c "gemini generateContent JSON" 200 "$(h -X POST "${GH[@]}" -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Return {\"ok\":true}"}]}],"generationConfig":{"responseMimeType":"application/json"}}' "$GB/models/$M:generateContent")"
c "supabase financial_records"  200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/financial_records?select=id&limit=1")"
c "supabase W5 columns (006)"   200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/financial_records?select=transaction_date,merchant,input_type,confidence,raw_input,created_by,reference_id&limit=1")"
ID=$(curl -s -X POST "${S[@]}" -H 'Content-Type: application/json' -H 'Prefer: return=representation' \
  -d '{"type":"expense","domain":"personal","amount":1,"source":"w5-probe","reference_id":"probe-'"$$"'"}' \
  "$SUPABASE_URL/rest/v1/financial_records" | python -c "import sys,json;print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
c "supabase write (insert)"     yes "$([[ -n "$ID" ]] && echo yes || echo no)"
c "supabase delete"             204 "$(h -X DELETE "${S[@]}" "$SUPABASE_URL/rest/v1/financial_records?id=eq.$ID")"
exit $f