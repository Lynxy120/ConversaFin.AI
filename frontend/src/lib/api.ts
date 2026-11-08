export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

type Init = Omit<RequestInit, "body"> & { json?: unknown };
type Q = Record<string, string | number | boolean | null | undefined>;

export const qs = (p: Q) => {
  const s = new URLSearchParams();
  for (const [k, v] of Object.entries(p))
    if (v !== undefined && v !== null && v !== "") s.set(k, String(v));
  const x = s.toString();
  return x ? `?${x}` : "";
};

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
    if (typeof window !== "undefined") 
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = "/login";
    throw new ApiError(401, "Session expired");
  }
  const text = await res.text();
  let data: { detail?: unknown } | null = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const d = data?.detail;
    const msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d
              .map(
                (e: { loc?: (string | number)[]; msg?: string }) =>
                  `${(e.loc ?? []).slice(1).join(".")}: ${e.msg}`,
              )
              .join("; ")
          : `HTTP ${res.status}`;
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

export const fetcher = <T>(path: string) => api<T>(path);
