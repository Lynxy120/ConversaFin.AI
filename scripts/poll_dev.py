import json, os, time, urllib.request
from pathlib import Path

for line in (Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
T, SECRET = os.environ["TELEGRAM_BOT_TOKEN"], os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
TARGET = os.getenv("POLL_TARGET", "http://localhost:8000/telegram/webhook")


def api(method, **p):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{T}/{method}",
        data=json.dumps(p).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=70))


api("deleteWebhook")
print("polling ->", TARGET)
off = 0
while True:
    try:
        res = api(
            "getUpdates",
            offset=off,
            timeout=30,
            allowed_updates=["message", "callback_query"],
        )["result"]
    except Exception as e:
        print("poll error:", e)
        time.sleep(3)
        continue
    for u in res:
        off = u["update_id"] + 1
        req = urllib.request.Request(
            TARGET,
            data=json.dumps(u).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Telegram-Bot-Api-Secret-Token": SECRET,
            },
        )
        try:
            print(u["update_id"], urllib.request.urlopen(req, timeout=10).status)
        except Exception as e:
            print("forward error:", e)
