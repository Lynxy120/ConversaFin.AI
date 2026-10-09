#!/usr/bin/env python3
"""W2 webhook validation. Requires backend at localhost:8000 with APP_ENV=development, WA_DRY_RUN=true.
Run: python scripts/test_w2_webhook.py"""
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 10
MAX_RESPONSE_SECONDS = 2.0
results: list[bool] = []


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env(Path(__file__).resolve().parent.parent / ".env")

VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "token_rahasia_webhook_123")
PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "1369280939600113")
APP_SECRET = os.getenv("WA_APP_SECRET", "")
OWNER_NUMBER = "".join(c for c in os.getenv("WA_OWNER_NUMBER", "").split(",")[0] if c.isdigit())
if OWNER_NUMBER.startswith("0"):
    OWNER_NUMBER = "62" + OWNER_NUMBER[1:]
CUSTOMER_NUMBER = "6281200000099"


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def request(method: str, path: str, *, params=None, body: bytes | None = None, headers=None):
    url = BASE + path + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode(), time.perf_counter() - start
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), time.perf_counter() - start
    except Exception as e:
        return 0, str(e), time.perf_counter() - start


def build_payload(sender: str, msg_id: str, text: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_TEST_ID",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550000000", "phone_number_id": PHONE_NUMBER_ID},
                    "contacts": [{"profile": {"name": "Test User"}, "wa_id": sender}],
                    "messages": [{
                        "from": sender,
                        "id": msg_id,
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {"body": text},
                    }],
                },
            }],
        }],
    }


def post_webhook(payload: dict, *, sign: bool = True, bad_signature: bool = False):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if APP_SECRET and sign:
        secret = APP_SECRET + "x" if bad_signature else APP_SECRET
        headers["X-Hub-Signature-256"] = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return request("POST", "/webhook", body=body, headers=headers)


def get_events() -> dict | None:
    code, body, _ = request("GET", "/webhook/debug/events")
    if code != 200:
        return None
    return json.loads(body)


def wait_for_event(msg_id: str, timeout: float = 10.0) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = get_events()
        if data:
            for ev in data["events"]:
                if ev["message_id"] == msg_id:
                    return ev
        time.sleep(0.25)
    return None


def test_verification() -> None:
    challenge = str(uuid.uuid4().int)[:12]
    code, body, _ = request("GET", "/webhook", params={
        "hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": challenge})
    record("GET /webhook valid token returns challenge", code == 200 and body == challenge, f"HTTP {code}, body={body[:40]!r}")

    code, _, _ = request("GET", "/webhook", params={
        "hub.mode": "subscribe", "hub.verify_token": "token_salah", "hub.challenge": challenge})
    record("GET /webhook invalid token rejected", code == 403, f"HTTP {code}")

    code, _, _ = request("GET", "/webhook", params={
        "hub.mode": "unsubscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": challenge})
    record("GET /webhook invalid mode rejected", code == 403, f"HTTP {code}")

    code, _, _ = request("GET", "/webhook")
    record("GET /webhook missing params rejected", code == 403, f"HTTP {code}")


def test_response_time() -> None:
    timings, codes = [], []
    for i in range(5):
        code, _, elapsed = post_webhook(build_payload(CUSTOMER_NUMBER, f"wamid.LAT_{uuid.uuid4().hex}", f"latency {i}"))
        timings.append(elapsed)
        codes.append(code)
    worst = max(timings)
    ok = all(c == 200 for c in codes) and worst < MAX_RESPONSE_SECONDS
    record("POST /webhook returns 200 in < 2s", ok, f"codes={sorted(set(codes))}, max={worst:.3f}s, avg={sum(timings)/len(timings):.3f}s")

    code, body, elapsed = post_webhook({"unexpected": "shape"})
    record("POST /webhook malformed payload returns 200 fast", code == 200 and elapsed < MAX_RESPONSE_SECONDS, f"HTTP {code}, {elapsed:.3f}s")

    if APP_SECRET:
        code, _, _ = post_webhook(build_payload(CUSTOMER_NUMBER, f"wamid.SIG_{uuid.uuid4().hex}", "bad sig"), bad_signature=True)
        record("POST /webhook invalid signature rejected", code == 403, f"HTTP {code}")


def test_background_routing() -> None:
    data = get_events()
    if data is None:
        record("Debug events endpoint reachable (APP_ENV=development)", False, "GET /webhook/debug/events failed")
        return
    record("Debug events endpoint reachable (APP_ENV=development)", True)

    if not data["dry_run"]:
        record("Backend running with WA_DRY_RUN=true", False, "set WA_DRY_RUN=true to avoid sending real WhatsApp messages")
        return
    record("Backend running with WA_DRY_RUN=true", True)

    if not OWNER_NUMBER:
        record("Owner routing", False, "WA_OWNER_NUMBER not set in .env")
        return

    owner_id = f"wamid.OWNER_{uuid.uuid4().hex}"
    cust_id = f"wamid.CUST_{uuid.uuid4().hex}"

    code_o, _, _ = post_webhook(build_payload(OWNER_NUMBER, owner_id, "Catat pemasukan 50000"))
    code_c, _, _ = post_webhook(build_payload(CUSTOMER_NUMBER, cust_id, "Halo, ada produk apa?"))
    record("Owner & Customer payloads accepted", code_o == 200 and code_c == 200, f"owner={code_o}, customer={code_c}")

    ev_o = wait_for_event(owner_id)
    record("Background task executed for Owner message", ev_o is not None, "no event within 10s" if ev_o is None else f"event={ev_o['handled_at']}")
    record("Owner message routed as role=owner", bool(ev_o) and ev_o["role"] == "owner" and ev_o["reply_ok"], str(ev_o and {k: ev_o[k] for k in ('role', 'reply_ok')}))

    ev_c = wait_for_event(cust_id)
    record("Background task executed for Customer message", ev_c is not None, "no event within 10s" if ev_c is None else f"event={ev_c['handled_at']}")
    record("Customer message routed as role=customer", bool(ev_c) and ev_c["role"] == "customer" and ev_c["reply_ok"], str(ev_c and {k: ev_c[k] for k in ('role', 'reply_ok')}))

    before = sum(1 for e in get_events()["events"] if e["message_id"] == owner_id)
    post_webhook(build_payload(OWNER_NUMBER, owner_id, "Catat pemasukan 50000"))
    time.sleep(1.5)
    after = sum(1 for e in get_events()["events"] if e["message_id"] == owner_id)
    record("Duplicate message_id deduplicated", before == after == 1, f"before={before}, after={after}")


if __name__ == "__main__":
    code, _, _ = request("GET", "/")
    if code != 200:
        print(f"[FAIL] Backend not reachable at {BASE} (HTTP {code})")
        sys.exit(1)
    print(f"[PASS] Backend reachable at {BASE}")
    test_verification()
    test_response_time()
    test_background_routing()
    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)