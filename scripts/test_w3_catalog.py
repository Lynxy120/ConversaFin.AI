#!/usr/bin/env python3
"""W3 catalog/cart validation (stdlib only).
Requires backend on localhost:8000 with APP_ENV=development, WA_DRY_RUN=true, ADMIN_API_KEY set.
Run: python scripts/test_w3_catalog.py"""
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

BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
API = BASE + "/api/v1"
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "")
APP_SECRET = os.getenv("WA_APP_SECRET", "")
PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "1369280939600113")
CATALOG_ID = os.getenv("WA_CATALOG_ID", "test_catalog")
OWNER = "".join(c for c in os.getenv("WA_OWNER_NUMBER", "").split(",")[0] if c.isdigit())
if OWNER.startswith("0"):
    OWNER = "62" + OWNER[1:]
CUSTOMER = "6281200000077"
RUN = uuid.uuid4().hex[:6].upper()
SKU_A, SKU_B = f"SKU-W3-{RUN}-A", f"SKU-W3-{RUN}-B"
PRICE_A, PRICE_B = 12500, 7500


def record(name: str, ok: bool, detail: str = "") -> None:
    passed = bool(ok)
    results.append(passed)
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def http(method, url, body=None, headers=None):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw, code = r.read().decode(), r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read().decode(), e.code
    except Exception as e:
        return 0, str(e), time.perf_counter() - start
    elapsed = time.perf_counter() - start
    try:
        return code, json.loads(raw), elapsed
    except ValueError:
        return code, raw, elapsed


def api(method, path, body=None, key=ADMIN_KEY):
    return http(method, API + path, body, {"X-API-Key": key} if key else {})


def post_webhook(payload: dict):
    raw = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if APP_SECRET:
        headers["X-Hub-Signature-256"] = "sha256=" + hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return http("POST", BASE + "/webhook", raw, headers)


def envelope(message: dict, sender: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{"id": "WABA_TEST", "changes": [{"field": "messages", "value": {
            "messaging_product": "whatsapp",
            "metadata": {"display_phone_number": "15550000000", "phone_number_id": PHONE_NUMBER_ID},
            "contacts": [{"profile": {"name": "W3 Tester"}, "wa_id": sender}],
            "messages": [message],
        }}]}],
    }


def text_payload(sender, msg_id, text):
    return envelope({"from": sender, "id": msg_id, "timestamp": str(int(time.time())),
                     "type": "text", "text": {"body": text}}, sender)


def order_payload(sender, msg_id, items):
    return envelope({"from": sender, "id": msg_id, "timestamp": str(int(time.time())), "type": "order",
                     "order": {"catalog_id": CATALOG_ID, "text": "Catatan test W3",
                               "product_items": [{"product_retailer_id": s, "quantity": q,
                                                  "item_price": 1, "currency": "IDR"} for s, q in items]}}, sender)


def events() -> list[dict]:
    code, body, _ = http("GET", BASE + "/webhook/debug/events")
    return body["events"] if code == 200 and isinstance(body, dict) else []


def wait_event(msg_id: str, timeout: float = 12.0):
    end = time.time() + timeout
    while time.time() < end:
        for ev in events():
            if ev["message_id"] == msg_id:
                return ev
        time.sleep(0.3)
    return None


def main() -> None:
    code, _, _ = http("GET", BASE + "/")
    if code != 200:
        print(f"[FAIL] Backend not reachable at {BASE} (HTTP {code})")
        sys.exit(1)
    code, body, _ = http("GET", BASE + "/webhook/debug/events")
    if code != 200 or not body.get("dry_run"):
        print("[FAIL] Need APP_ENV=development and WA_DRY_RUN=true")
        sys.exit(1)
    if not ADMIN_KEY or not OWNER:
        print("[FAIL] ADMIN_API_KEY and WA_OWNER_NUMBER must be set in .env")
        sys.exit(1)
    print(f"[PASS] Backend reachable, dry-run active, run={RUN}")

    # --- 1. Auth & validation
    code, _, _ = api("POST", "/products", {"retailer_id": SKU_A, "name": "x", "price": 1}, key="")
    record("POST /products without API key -> 401", code == 401, f"HTTP {code}")
    code, _, _ = api("POST", "/products", {"retailer_id": SKU_A, "name": "x", "price": 1}, key="wrong")
    record("POST /products wrong API key -> 401", code == 401, f"HTTP {code}")
    code, _, _ = api("POST", "/products", {"retailer_id": "bad sku!", "name": "x", "price": -5})
    record("POST /products invalid body -> 422", code == 422, f"HTTP {code}")
    code, _, _ = api("GET", "/orders", key="")
    record("GET /orders without API key -> 401", code == 401, f"HTTP {code}")

    # --- 2. Product CRUD
    ids = {}
    for sku, name, price in ((SKU_A, "W3 Test Produk A", PRICE_A), (SKU_B, "W3 Test Produk B", PRICE_B)):
        code, body, _ = api("POST", "/products", {
            "retailer_id": sku, "name": name, "description": "w3 test", "price": price,
            "image_url": "https://placehold.co/600x600.png"})
        ok = code == 201 and isinstance(body, dict) and body.get("retailer_id") == sku
        record(f"POST /products {sku} -> 201", ok, f"HTTP {code}")
        if ok:
            ids[sku] = body["id"]
    code, _, _ = api("POST", "/products", {"retailer_id": SKU_A, "name": "dup", "price": 1})
    record("POST /products duplicate retailer_id -> 409", code == 409, f"HTTP {code}")
    code, body, _ = http("GET", API + "/products")
    listed = {p["retailer_id"] for p in body} if code == 200 and isinstance(body, list) else set()
    record("GET /products (public) lists new SKUs", {SKU_A, SKU_B} <= listed, f"HTTP {code}")
    if len(ids) < 2:
        print("[FAIL] Product creation failed; aborting remaining tests")
        sys.exit(1)

    # --- 3. Catalog request routing
    mid = f"wamid.CAT_{uuid.uuid4().hex}"
    code, _, elapsed = post_webhook(text_payload(CUSTOMER, mid, "katalog"))
    record("POST /webhook 'katalog' -> 200 < 2s", code == 200 and elapsed < 2.0, f"HTTP {code}, {elapsed:.3f}s")
    ev = wait_event(mid)
    record("Customer 'katalog' -> action=catalog_sent", bool(ev) and ev["action"] == "catalog_sent" and ev["reply_ok"],
           str(ev and {k: ev[k] for k in ("role", "action", "reply_ok")}))

    # --- 4. Multi-product cart order (tampered payload price must be ignored)
    oid = f"wamid.ORD_{uuid.uuid4().hex}"
    code, _, elapsed = post_webhook(order_payload(CUSTOMER, oid, [(SKU_A, 2), (SKU_B, 1)]))
    record("POST /webhook order payload -> 200 < 2s", code == 200 and elapsed < 2.0, f"HTTP {code}, {elapsed:.3f}s")
    ev = wait_event(oid)
    record("Order -> action=order_created", bool(ev) and ev["action"] == "order_created" and ev["reply_ok"] and ev["order_id"],
           str(ev and {k: ev[k] for k in ("role", "action", "order_id")}))
    if ev and ev.get("order_id"):
        code, order, _ = api("GET", f"/orders/{ev['order_id']}")
        expected = 2 * PRICE_A + PRICE_B
        items = order.get("order_items", []) if isinstance(order, dict) else []
        record("Order total from DB prices (tamper-proof)", code == 200 and float(order["total_price"]) == expected,
               f"total={order.get('total_price') if isinstance(order, dict) else order}, expected={expected}")
        record("Order header fields", isinstance(order, dict) and order.get("status") == "pending"
               and order.get("customer_phone") == CUSTOMER and order.get("quantity") == 3
               and order.get("wa_message_id") == oid,
               str(isinstance(order, dict) and {k: order.get(k) for k in ("status", "customer_phone", "quantity")}))
        by_sku = {i["retailer_id"]: i for i in items}
        record("Order items persisted (2 lines, correct subtotals)",
               len(items) == 2 and float(by_sku[SKU_A]["subtotal"]) == 2 * PRICE_A and float(by_sku[SKU_B]["subtotal"]) == PRICE_B,
               f"{len(items)} items")

    # --- 5. Idempotency
    post_webhook(order_payload(CUSTOMER, oid, [(SKU_A, 2), (SKU_B, 1)]))
    time.sleep(1.5)
    n_events = sum(1 for e in events() if e["message_id"] == oid)
    code, rows, _ = api("GET", "/orders?limit=100")
    n_orders = sum(1 for o in rows if o.get("wa_message_id") == oid) if code == 200 else -1
    record("Duplicate order message deduplicated", n_events == 1 and n_orders == 1, f"events={n_events}, orders={n_orders}")

    # --- 6. Rejection path
    bad = f"wamid.BAD_{uuid.uuid4().hex}"
    post_webhook(order_payload(CUSTOMER, bad, [(f"SKU-NOPE-{RUN}", 1)]))
    ev = wait_event(bad)
    record("Unknown SKU -> action=order_rejected, no order", bool(ev) and ev["action"] == "order_rejected" and not ev["order_id"],
           str(ev and {k: ev[k] for k in ("action", "order_id")}))

    # --- 7. Owner routing
    oo = f"wamid.OWNORD_{uuid.uuid4().hex}"
    post_webhook(order_payload(OWNER, oo, [(SKU_B, 1)]))
    ev = wait_event(oo)
    record("Owner order -> role=owner, order_created", bool(ev) and ev["role"] == "owner" and ev["action"] == "order_created",
           str(ev and {k: ev[k] for k in ("role", "action")}))
    oc = f"wamid.OWNCMD_{uuid.uuid4().hex}"
    post_webhook(text_payload(OWNER, oc, "/orders"))
    ev = wait_event(oc)
    record("Owner '/orders' command -> action=owner_orders", bool(ev) and ev["role"] == "owner" and ev["action"] == "owner_orders",
           str(ev and {k: ev[k] for k in ("role", "action")}))
    cc = f"wamid.CUSTCMD_{uuid.uuid4().hex}"
    post_webhook(text_payload(CUSTOMER, cc, "/orders"))
    ev = wait_event(cc)
    record("Customer '/orders' NOT treated as owner command", bool(ev) and ev["role"] == "customer" and ev["action"] == "customer_reply",
           str(ev and {k: ev[k] for k in ("role", "action")}))

    # --- 8. Cleanup (soft delete)
    for sku, pid in ids.items():
        code, _, _ = api("DELETE", f"/products/{pid}")
        record(f"DELETE /products/{sku} -> 200", code == 200, f"HTTP {code}")
    code, body, _ = http("GET", API + "/products")
    still = {p["retailer_id"] for p in body} if code == 200 else {"?"}
    record("Deactivated products hidden from public list", not ({SKU_A, SKU_B} & still))

    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()