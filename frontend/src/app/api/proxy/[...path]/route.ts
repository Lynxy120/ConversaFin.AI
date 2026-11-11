import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60; // Render free tier cold start

const ALLOWED = new Set(["products", "orders", "finance", "bot"]);

async function handle(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  if (!ALLOWED.has(path[0]) || path.some((s) => s === ".." || s === ".")) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const url = `${process.env.API_URL}/api/v1/${path.map(encodeURIComponent).join("/")}${req.nextUrl.search}`;
  const hasBody = !["GET", "HEAD"].includes(req.method);
  try {
    const up = await fetch(url, {
      method: req.method,
      headers: {
        "X-API-Key": process.env.ADMIN_API_KEY ?? "",
        ...(hasBody ? { "Content-Type": "application/json" } : {}),
      },
      body: hasBody ? await req.text() : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(55_000),
    });
    return new NextResponse(await up.text(), {
      status: up.status,
      headers: {
        "Content-Type": up.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 },
    );
  }
}

export { handle as GET, handle as POST, handle as PATCH, handle as DELETE };
