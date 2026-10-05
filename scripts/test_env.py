#!/usr/bin/env python3
"""W1 environment verification. Run: python scripts/test_env.py"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIRED = [
    "SUPABASE_URL", "SUPABASE_KEY",
    "GEMINI_API_KEY",
    "WA_PHONE_NUMBER_ID", "WA_ACCESS_TOKEN", "WA_VERIFY_TOKEN",
    "MIDTRANS_SERVER_KEY", "MIDTRANS_CLIENT_KEY",
]
PLACEHOLDERS = ("your-", "xxxxxxxx", "SB-Mid-server-xxx", "SB-Mid-client-xxx")
TIMEOUT = 10
results = []


def load_env(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def http(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)


def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def check_vars():
    for key in REQUIRED:
        val = os.getenv(key, "")
        ok = bool(val) and not any(val.startswith(p) or p in val for p in PLACEHOLDERS)
        record(f"ENV {key}", ok, "" if ok else "missing or placeholder")


def check_supabase():
    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_KEY", "")
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    for table in ("products", "orders", "financial_records"):
        code, body = http(f"{url}/rest/v1/{table}?select=id&limit=1", h)
        record(f"Supabase table '{table}'", code == 200, f"HTTP {code}" + ("" if code == 200 else f" {body[:120]}"))


def check_gemini():
    key = os.getenv("GEMINI_API_KEY", "")
    code, body = http(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
    detail = f"HTTP {code}"
    if code == 200:
        detail += f", {len(json.loads(body).get('models', []))} models"
    record("Gemini API connectivity", code == 200, detail)

    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    payload = json.dumps({"contents": [{"parts": [{"text": "Reply with: OK"}]}]}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        data=payload, headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT * 2) as r:
            text = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
            record(f"Gemini generateContent ({model})", True, text.strip()[:30])
    except urllib.error.HTTPError as e:
        record(f"Gemini generateContent ({model})", False, f"HTTP {e.code} {e.read().decode()[:120]}")
    except Exception as e:
        record(f"Gemini generateContent ({model})", False, str(e))


def check_whatsapp():
    pid, token = os.getenv("WA_PHONE_NUMBER_ID", ""), os.getenv("WA_ACCESS_TOKEN", "")
    code, body = http(f"https://graph.facebook.com/v20.0/{pid}?fields=display_phone_number,verified_name",
                      {"Authorization": f"Bearer {token}"})
    record("Meta WhatsApp Cloud API", code == 200, f"HTTP {code}" + ("" if code == 200 else f" {body[:120]}"))


def check_midtrans():
    server_key = os.getenv("MIDTRANS_SERVER_KEY", "")
    prod = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
    base = "https://api.midtrans.com" if prod else "https://api.sandbox.midtrans.com"
    auth = base64.b64encode(f"{server_key}:".encode()).decode()
    # Non-existent order: 404 = key authenticated (valid); 401 = invalid key.
    code, body = http(f"{base}/v2/conversafin-w1-healthcheck/status",
                      {"Authorization": f"Basic {auth}", "Accept": "application/json"})
    try:
        inner = int(json.loads(body).get("status_code", code))
    except Exception:
        inner = code
    ok = code != 401 and inner != 401 and code != 0
    record(f"Midtrans server key ({'production' if prod else 'sandbox'})", ok, f"HTTP {code}, status_code {inner}")


def check_backend():
    code, _ = http("http://localhost:8000/")
    record("Backend GET / (localhost:8000)", code == 200, f"HTTP {code}")


if __name__ == "__main__":
    load_env(Path(__file__).resolve().parent.parent / ".env")
    check_vars()
    check_supabase()
    check_gemini()
    check_whatsapp()
    check_midtrans()
    check_backend()
    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)