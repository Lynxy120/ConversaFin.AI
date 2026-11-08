export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

type Init = Omit<RequestInit, "body"> & { json?: unknown };

export async function api<T>(
  path: string,
  { json, ...init }: Init = {},
): Promise<T> {
  const res = await fetch(`/api/proxy${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
    body: json !== undefined ? JSON.stringify(json) : undefined,
  });
  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Sesi berakhir");
  }
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const d = (data as { detail?: unknown } | null)?.detail;
    throw new ApiError(
      res.status,
      typeof d === "string" ? d : `HTTP ${res.status}`,
    );
  }
  return data as T;
}

export const fetcher = <T>(path: string) => api<T>(path);
// usage: useSWR<Summary>("/finance/summary?from=2026-11-01&to=2026-11-08")
//        await api("/products", { method: "POST", json: {...} })
