#!/usr/bin/env bash
cd "$(dirname "$0")/.."; sed -i 's/\r$//' .env; set -a; source .env; set +a
G="https://graph.facebook.com/${WA_GRAPH_VERSION:-v23.0}"; A="Authorization: Bearer $WA_ACCESS_TOKEN"
S=(-H "apikey: $SUPABASE_KEY" -H "Authorization: Bearer $SUPABASE_KEY"); f=0
c(){ [[ "$3" == "$2" ]] && echo "[PASS] $1" || { echo "[FAIL] $1 (got $3, want $2)"; f=1; }; }
h(){ curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$@"; }

c "supabase products"      200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/products?select=id,sku,is_active&limit=1")"
c "supabase orders (W4)"   200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/orders?select=id,paid_at,receipt_path,midtrans_order_id&limit=1")"
c "supabase order_items"   200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/order_items?select=id&limit=1")"
c "supabase cart_items"    200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/cart_items?select=customer_phone&limit=1")"
c "supabase fin_records"   200 "$(h "${S[@]}" "$SUPABASE_URL/rest/v1/financial_records?select=reference_id&limit=1")"
c "supabase storage"       200 "$(h "${S[@]}" "$SUPABASE_URL/storage/v1/bucket")"
c "supabase rpc add_to_cart exists" 400 "$(h -X POST "${S[@]}" -H 'Content-Type: application/json' -d '{"p_phone":"0","p_sku":"__none__"}' "$SUPABASE_URL/rest/v1/rpc/add_to_cart")"
c "wa phone number"        200 "$(h -H "$A" "$G/$WA_PHONE_NUMBER_ID?fields=display_phone_number,verified_name")"
c "wa waba subscribed_apps" 200 "$(h -H "$A" "$G/$WA_WABA_ID/subscribed_apps")"
c "midtrans server key"    404 "$(curl -s -u "$MIDTRANS_SERVER_KEY:" https://api.sandbox.midtrans.com/v2/CF-KEYCHECK/status | python -c "import sys,json;print(json.load(sys.stdin).get('status_code'))")"
c "midtrans QRIS charge"   201 "$(curl -s -X POST -u "$MIDTRANS_SERVER_KEY:" -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"payment_type":"qris","transaction_details":{"order_id":"CF-VERIFY-'$(date +%s)'","gross_amount":10000},"qris":{"acquirer":"gopay"}}' \
  https://api.sandbox.midtrans.com/v2/charge | python -c "import sys,json;print(json.load(sys.stdin).get('status_code'))")"
c "render backend /"       200 "$(h https://conversafin-ai.onrender.com/)"
exit $f