import { NextResponse } from "next/server";
import { COOKIE, TTL, createToken, safeEq } from "@/lib/session";

export async function POST(req: Request) {
  const { user = "", pass = "" } = await req.json().catch(() => ({}));
  const [u, p] = await Promise.all([
    safeEq(String(user), process.env.DASH_USER ?? ""),
    safeEq(String(pass), process.env.DASH_PASS ?? ""),
  ]);
  if (!(u && p && process.env.DASH_PASS && process.env.SESSION_SECRET)) {
    await new Promise((r) => setTimeout(r, 500));
    return NextResponse.json(
      { detail: "Username atau password salah" },
      { status: 401 },
    );
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE, await createToken(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: TTL,
  });
  return res;
}
