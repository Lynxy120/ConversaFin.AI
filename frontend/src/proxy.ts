import { NextRequest, NextResponse } from "next/server";
import { COOKIE, verifyToken } from "@/lib/session";

const PUBLIC = [
  /^\/login$/,
  /^\/api\/auth\//,
  /^\/manifest\.json$/,
  /^\/sw\.js$/,
  /^\/offline\.html$/,
  /^\/icons\//,
  /^\/favicon\.ico$/,
];

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (PUBLIC.some((r) => r.test(pathname))) return NextResponse.next();
  if (await verifyToken(req.cookies.get(COOKIE)?.value))
    return NextResponse.next();
  if (pathname.startsWith("/api/"))
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const url = req.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  url.searchParams.set("next", pathname);
  return NextResponse.redirect(url);
}

export const config = { matcher: ["/((?!_next/static|_next/image).*)"] };
