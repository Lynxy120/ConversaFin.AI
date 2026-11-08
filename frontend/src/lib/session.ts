const enc = new TextEncoder();
export const COOKIE = "cf_session";
export const TTL = 60 * 60 * 24 * 7;

const hex = (b: ArrayBuffer) =>
  [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
const hmac = async (msg: string) => {
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(process.env.SESSION_SECRET ?? ""),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return hex(await crypto.subtle.sign("HMAC", key, enc.encode(msg)));
};

export async function safeEq(a: string, b: string): Promise<boolean> {
  const [x, y] = await Promise.all(
    [a, b].map(
      async (s) =>
        new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(s))),
    ),
  );
  let d = 0;
  for (let i = 0; i < 32; i++) d |= x[i] ^ y[i];
  return d === 0;
}

export async function createToken(): Promise<string> {
  const exp = String(Math.floor(Date.now() / 1000) + TTL);
  return `${exp}.${await hmac(exp)}`;
}

export async function verifyToken(t?: string): Promise<boolean> {
  if (!t || !process.env.SESSION_SECRET) return false;
  const [exp, sig] = t.split(".");
  if (!exp || !sig || Number(exp) < Date.now() / 1000) return false;
  return safeEq(await hmac(exp), sig);
}
