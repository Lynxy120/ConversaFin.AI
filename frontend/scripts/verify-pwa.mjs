const base = (process.argv[2] ?? "http://localhost:3000").replace(/\/$/, "");
let fail = 0;
const ok = (n, c, d = "") => { console.log(`[${c ? "PASS" : "FAIL"}] ${n}${d ? ` -> ${d}` : ""}`); if (!c) fail = 1; };
const get = (p, o = {}) => fetch(base + p, { redirect: "manual", ...o });

const m = await get("/manifest.json");
ok("manifest.json 200", m.status === 200, `${m.status} ${m.headers.get("content-type")}`);
const j = await m.json().catch(() => ({}));
for (const k of ["name", "short_name", "start_url", "scope", "theme_color", "background_color"]) ok(`manifest.${k}`, !!j[k], String(j[k]));
ok("display=standalone", j.display === "standalone");
ok("theme_color=#0EA5E9", String(j.theme_color).toUpperCase() === "#0EA5E9");
const icons = j.icons ?? [];
ok("icons 192+512 (any)", ["192x192", "512x512"].every((s) => icons.some((i) => i.sizes === s && i.purpose === "any")));
ok("maskable icon", icons.some((i) => i.purpose === "maskable"));
for (const i of icons) {
  const r = await get(i.src);
  ok(`icon ${i.src}`, r.status === 200 && (r.headers.get("content-type") ?? "").includes("image/png"), String(r.status));
}
const sw = await get("/sw.js");
ok("sw.js 200 + no-cache", sw.status === 200 && /no-cache|no-store/.test(sw.headers.get("cache-control") ?? ""), `${sw.status} ${sw.headers.get("cache-control")}`);
ok("offline.html 200", (await get("/offline.html")).status === 200);
const login = await get("/login");
ok("/login 200 + <link rel=manifest>", login.status === 200 && (await login.text()).includes('rel="manifest"'));
const home = await get("/");
ok("auth gate: / -> redirect /login", [302, 307, 308].includes(home.status) && (home.headers.get("location") ?? "").includes("/login"), String(home.status));
ok("auth gate: /api/proxy/products -> 401", (await get("/api/proxy/products")).status === 401);
ok("auth gate: /api/health -> 401", (await get("/api/health")).status === 401);
process.exit(fail);