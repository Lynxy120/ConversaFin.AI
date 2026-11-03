import { NextRequest, NextResponse } from "next/server";

export function middleware(req: NextRequest) {
  const b64 = (req.headers.get("authorization") ?? "").split(" ")[1];
  if (b64 && atob(b64) === `${process.env.DASH_USER}:${process.env.DASH_PASS}`)
    return NextResponse.next();
  return new NextResponse("Auth required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="admin"' },
  });
}
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
