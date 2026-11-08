const { API_URL, ADMIN_API_KEY, SUPABASE_URL, SUPABASE_KEY } = process.env;
let fail = 0;
const t = async (name, url, { want = 200, headers = {}, method = "GET", body, wait = 20_000 } = {}) => {
  const s = performance.now();
  try {
    const r = await fetch(url, { method, headers, body, signal: AbortSignal.timeout(wait) });
    const good = r.status === want;
    console.log(`[${good ? "PASS" : "FAIL"}] ${name} (${r.status}, ${Math.round(performance.now() - s)}ms)`);
    if (!good) fail = 1;
    return r;
  } catch (e) { console.log(`[FAIL] ${name} (${e.name})`); fail = 1; }
};
if (!API_URL || !ADMIN_API_KEY) { console.log("[FAIL] API_URL / ADMIN_API_KEY missing"); process.exit(1); }

const A = { "X-API-Key": ADMIN_API_KEY };
const to = new Date().toISOString().slice(0, 10);
const from = new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10);
const q = `from=${from}&to=${to}`;

await t("render wake + health", `${API_URL}/`, { wait: 90_000 });
await t("GET /products (public)", `${API_URL}/api/v1/products`);
await t("GET /products/all (admin)", `${API_URL}/api/v1/products/all`, { headers: A });
await t("GET /orders (admin)", `${API_URL}/api/v1/orders?limit=1`, { headers: A });
await t("GET /orders no key -> 401", `${API_URL}/api/v1/orders`, { want: 401 });
await t("GET /finance/summary", `${API_URL}/api/v1/finance/summary?${q}`, { headers: A });
await t("GET /finance/records", `${API_URL}/api/v1/finance/records?${q}&limit=5`, { headers: A });
await t("GET /finance/records bad range -> 422", `${API_URL}/api/v1/finance/records?from=2026-12-01&to=2026-11-01`, { headers: A, want: 422 });
await t("GET /finance/summary no key -> 401", `${API_URL}/api/v1/finance/summary`, { want: 401 });

if (SUPABASE_URL && SUPABASE_KEY) {
  const S = { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` };
  for (const tb of ["products", "orders", "financial_records"])
    await t(`supabase table ${tb}`, `${SUPABASE_URL}/rest/v1/${tb}?select=id&limit=1`, { headers: S });
  await t("supabase rpc finance_timeseries", `${SUPABASE_URL}/rest/v1/rpc/finance_timeseries`, {
    method: "POST", headers: { ...S, "Content-Type": "application/json" },
    body: JSON.stringify({ p_from: from, p_to: to, p_domain: null }),
  });
  await t("supabase rpc finance_by_category", `${SUPABASE_URL}/rest/v1/rpc/finance_by_category`, {
    method: "POST", headers: { ...S, "Content-Type": "application/json" },
    body: JSON.stringify({ p_from: from, p_to: to, p_domain: null }),
  });
} else console.log("[SKIP] Supabase direct checks (SUPABASE_URL/KEY not in env)");
process.exit(fail);