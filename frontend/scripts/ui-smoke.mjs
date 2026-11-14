import { chromium } from "playwright";

const base = (process.argv[2] ?? "http://localhost:3000").replace(/\/$/, "");
const { DASH_USER: u, DASH_PASS: p } = process.env;
let fail = 0;
const ok = (n, c, d = "") => {
  console.log(`[${c ? "PASS" : "FAIL"}] ${n}${d ? ` -> ${d}` : ""}`);
  if (!c) fail = 1;
};
const b = await chromium.launch({
  executablePath:
    "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
});

for (const [vn, vp] of [
  ["desktop", { width: 1280, height: 800 }],
  ["mobile", { width: 390, height: 844 }],
]) {
  for (const scheme of ["light", "dark"]) {
    const ctx = await b.newContext({ viewport: vp, colorScheme: scheme });
    const pg = await ctx.newPage();
    const errs = [];
    pg.on("pageerror", (e) => errs.push(e.message));
    pg.on(
      "console",
      (m) =>
        m.type() === "error" &&
        !/Failed to load resource.*(401|502)/.test(m.text()) &&
        errs.push(m.text()),
    );

    await pg.goto(`${base}/login`);
    await pg.fill("input[name=user]", u ?? "");
    await pg.fill("input[name=pass]", p ?? "");
    await pg.click("button[type=submit]");
    await pg.waitForURL(`${base}/`, { timeout: 60000 });

    for (const path of ["/", "/catalog", "/transactions", "/settings"]) {
      await pg.goto(base + path);
      await pg.waitForTimeout(2000);
      const t = `${vn}/${scheme}${path}`;
      ok(
        `${t} data-theme=${scheme}`,
        (await pg.evaluate(() => document.documentElement.dataset.theme)) ===
          scheme,
      );
      ok(
        `${t} no horizontal scroll`,
        await pg.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      ok(
        `${t} glass blur applied`,
        await pg.evaluate(() =>
          [...document.querySelectorAll(".glass")].some((e) =>
            getComputedStyle(e).backdropFilter.includes("blur"),
          ),
        ),
      );
      ok(
        `${t} nav visible (${vn === "desktop" ? "sidebar" : "bottom bar"})`,
        await pg
          .locator(vn === "desktop" ? "aside" : "nav[aria-label=Mobile]")
          .first()
          .isVisible(),
      );
    }
    await pg.goto(base + "/");
    await pg.click("button[aria-label='Toggle theme']");
    ok(
      `${vn}/${scheme} toggle flips theme`,
      (await pg.evaluate(() => document.documentElement.dataset.theme)) !==
        scheme,
    );
    ok(
      `${vn}/${scheme} no console errors`,
      errs.length === 0,
      errs.slice(0, 2).join(" | "),
    );
    await ctx.close();
  }
}
await b.close();
process.exit(fail);
