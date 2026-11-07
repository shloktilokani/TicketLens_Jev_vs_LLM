// The one HTTP client for the TicketLens backend. The browser never calls Jev or OpenAI.
export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

type Detail = { loc?: (string | number)[]; msg?: string }

function messageFrom(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    // FastAPI validation errors: "field: message" for each problem.
    return (detail as Detail[])
      .map((d) => [d.loc?.slice(1).join("."), d.msg].filter(Boolean).join(": "))
      .join("; ")
  }
  return `Request failed (${status})`
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = init.body
    ? { "Content-Type": "application/json", ...init.headers }
    : init.headers
  let response: Response
  try {
    response = await fetch(BASE_URL + path, { ...init, headers })
  } catch {
    throw new ApiError(
      "Cannot reach the TicketLens backend. Is it running on 127.0.0.1:8000?",
      0,
    )
  }
  if (response.status === 204) return undefined as T
  const body = await response.json().catch(() => null)
  if (!response.ok)
    throw new ApiError(messageFrom(body, response.status), response.status)
  return body as T
}

export const send = <T>(method: string, path: string, data?: unknown) =>
  api<T>(path, {
    method,
    body: data === undefined ? undefined : JSON.stringify(data),
  })
