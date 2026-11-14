const E = process.env;
let fail = 0;

const run = async (name, url, { method = "GET", headers = {}, body, ms = 30000, ok = (r) => r.status === 200 } = {}) => {
  const s = performance.now();
  try {
    const r = await fetch(url, { method, headers, body, signal: AbortSignal.timeout(ms) });
    const j = await r.json().catch(() => null);
    const good = await ok(r, j);
    console.log(`[${good ? "PASS" : "FAIL"}] ${name} (${r.status}, ${Math.round(performance.now() - s)}ms)`);
    if (!good) fail = 1;
    return j;
  } catch (e) {
    console.log(`[FAIL] ${name} (${e.name})`);
    fail = 1;
  }
};

const need = ["TELEGRAM_BOT_TOKEN", "SUPABASE_URL", "SUPABASE_KEY", "MIDTRANS_SERVER_KEY", "GEMINI_API_KEY", "GEMINI_MODEL"].filter((k) => !E[k]);
if (need.length) { console.log("[FAIL] missing env:", need.join(", ")); process.exit(1); }

// Telegram
const me = await run("telegram getMe", `https://api.telegram.org/bot${E.TELEGRAM_BOT_TOKEN}/getMe`, { ok: (r, j) => r.status === 200 && j?.ok });
if (me) console.log(`       bot: @${me.result.username}`);
const wh = await run("telegram getWebhookInfo", `https://api.telegram.org/bot${E.TELEGRAM_BOT_TOKEN}/getWebhookInfo`, { ok: (r, j) => j?.ok });
if (wh) console.log(`       webhook: ${wh.result.url || "(not set)"} | pending: ${wh.result.pending_update_count} | last_error: ${wh.result.last_error_message ?? "none"}`);

// Supabase
const S = { apikey: E.SUPABASE_KEY, Authorization: `Bearer ${E.SUPABASE_KEY}` };
for (const t of ["products", "orders", "order_items", "cart_items", "financial_records"])
  await run(`supabase table ${t}`, `${E.SUPABASE_URL}/rest/v1/${t}?select=*&limit=1`, { headers: S });
await run("supabase storage buckets", `${E.SUPABASE_URL}/storage/v1/bucket`, { headers: S });
const d = new Date().toISOString().slice(0, 10);
await run("supabase rpc finance_timeseries", `${E.SUPABASE_URL}/rest/v1/rpc/finance_timeseries`, {
  method: "POST", headers: { ...S, "Content-Type": "application/json" }, body: JSON.stringify({ p_from: d, p_to: d, p_domain: null }),
});

// Midtrans (status endpoint answers HTTP 200 with body status_code "404" when the key is valid, "401" when it is not)
const mtBase = E.MIDTRANS_IS_PRODUCTION === "true" ? "https://api.midtrans.com" : "https://api.sandbox.midtrans.com";
const mtAuth = { Authorization: "Basic " + Buffer.from(`${E.MIDTRANS_SERVER_KEY}:`).toString("base64"), Accept: "application/json" };
await run("midtrans server key auth", `${mtBase}/v2/CF-KEYCHECK/status`, { headers: mtAuth, ok: (_, j) => String(j?.status_code) === "404" });
await run("midtrans QRIS charge", `${mtBase}/v2/charge`, {
  method: "POST", headers: { ...mtAuth, "Content-Type": "application/json" },
  body: JSON.stringify({ payment_type: "qris", transaction_details: { order_id: `CF-CHK-${Date.now()}`, gross_amount: 10000 }, qris: { acquirer: "gopay" } }),
  ok: (_, j) => String(j?.status_code) === "201",
});

// Gemini
const G = { "x-goog-api-key": E.GEMINI_API_KEY, "Content-Type": "application/json" };
const gb = "https://generativelanguage.googleapis.com/v1beta";
await run(`gemini model ${E.GEMINI_MODEL}`, `${gb}/models/${E.GEMINI_MODEL}`, { headers: G });
await run("gemini generateContent", `${gb}/models/${E.GEMINI_MODEL}:generateContent`, {
  method: "POST", headers: G, body: JSON.stringify({ contents: [{ parts: [{ text: "Reply OK" }] }] }),
});

// Backend + frontend
const API = E.API_URL ?? "https://conversafin-ai.onrender.com";
await run("backend GET / (Render, allow cold start)", `${API}/`, { ms: 90000 });
if (E.ADMIN_API_KEY) {
  const A = { "X-API-Key": E.ADMIN_API_KEY };
  await run("backend /finance/summary", `${API}/api/v1/finance/summary`, { headers: A });
  await run("backend /products/all", `${API}/api/v1/products/all?limit=1`, { headers: A });
  await run("backend /bot/status", `${API}/api/v1/bot/status`, { headers: A });
  await run("backend no key -> 401", `${API}/api/v1/orders`, { ok: (r) => r.status === 401 });
}
const FE = E.FRONTEND_URL ?? "https://conversafin-ai.vercel.app";
await run("frontend /login", `${FE}/login`, { ok: (r) => r.status === 200 });
await run("frontend /manifest.json", `${FE}/manifest.json`, { ok: (r) => r.status === 200 });

process.exit(fail);