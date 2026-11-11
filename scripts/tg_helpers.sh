cd "$(git rev-parse --show-toplevel)"; sed -i 's/\r$//' .env; set -a; source .env; set +a
API=http://localhost:8000/api/v1; ADM=(-H "X-API-Key: $ADMIN_API_KEY"); J=(-H "Content-Type: application/json")
SB=(-H "apikey: $SUPABASE_KEY" -H "Authorization: Bearer $SUPABASE_KEY")
TID=${TID:-${TELEGRAM_OWNER_IDS%%,*}}                      # owner by default; `TID=555000111` simulates a customer
FROM='{"id":'$TID',"is_bot":false,"first_name":"Tester"}'
tg_post(){ curl -s -X POST localhost:8000/telegram/webhook "${J[@]}" -H "X-Telegram-Bot-Api-Secret-Token: $TELEGRAM_WEBHOOK_SECRET" -d "$1" -w " HTTP %{http_code} %{time_total}s\n"; }
tg_msg(){ tg_post '{"update_id":'$RANDOM$RANDOM',"message":{"message_id":'$RANDOM',"from":'"$FROM"',"chat":{"id":'$TID',"type":"private"},"date":1,"text":"'"$1"'"}}'; }
tg_cb(){ tg_post '{"update_id":'$RANDOM$RANDOM',"callback_query":{"id":"'$RANDOM'","from":'"$FROM"',"message":{"message_id":7,"from":{"id":1,"is_bot":true,"first_name":"bot"},"chat":{"id":'$TID',"type":"private"},"date":1},"data":"'"$1"'"}}'; }
ev(){ sleep "${1:-2}"; curl -s localhost:8000/telegram/debug/events | python -c "import sys,json;[print(e['action'],e['role'],e['ok'],e['order_id'] or '') for e in json.load(sys.stdin)['events'][-${2:-3}:]]"; }