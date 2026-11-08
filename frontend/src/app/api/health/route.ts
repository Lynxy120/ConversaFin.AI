import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function GET() {
  const t = performance.now();
  try {
    const r = await fetch(`${process.env.API_URL}/`, {
      cache: "no-store",
      signal: AbortSignal.timeout(55_000),
    });
    return NextResponse.json({
      ok: r.ok,
      status: r.status,
      ms: Math.round(performance.now() - t),
    });
  } catch {
    return NextResponse.json({
      ok: false,
      status: 0,
      ms: Math.round(performance.now() - t),
    });
  }
}
