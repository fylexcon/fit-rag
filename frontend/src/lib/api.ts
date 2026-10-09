import type {
  ActivityDetail,
  ActivityList,
  HealthSummary,
  User,
  WorkoutSubmission,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const TOKEN_KEY = "fitrag.token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Token storage -------------------------------------------------------
// Backed by localStorage, exposed as a tiny external store so React can
// subscribe with useSyncExternalStore.

const listeners = new Set<() => void>();

export const tokenStore = {
  get(): string | null {
    try {
      return window.localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string | null) {
    try {
      if (token) window.localStorage.setItem(TOKEN_KEY, token);
      else window.localStorage.removeItem(TOKEN_KEY);
    } catch {
      // Storage unavailable (private mode); the session just won't persist.
    }
    listeners.forEach((l) => l());
  },
  subscribe(listener: () => void) {
    listeners.add(listener);
    const onStorage = (e: StorageEvent) => {
      if (e.key === TOKEN_KEY) listener();
    };
    window.addEventListener("storage", onStorage);
    return () => {
      listeners.delete(listener);
      window.removeEventListener("storage", onStorage);
    };
  },
};

// --- Request helper ------------------------------------------------------

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit | object | null;
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let body = options.body as BodyInit | null | undefined;
  const isNativeBody =
    body instanceof FormData || body instanceof URLSearchParams || typeof body === "string";
  if (body != null && !isNativeBody) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers, body });

  if (res.status === 401 && token) {
    // Expired or revoked token: drop it so the UI routes back to /login.
    tokenStore.set(null);
  }
  if (!res.ok) {
    throw new ApiError(res.status, await errorMessage(res));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ");
    }
  } catch {
    // Non-JSON error body.
  }
  return `Request failed (${res.status})`;
}

// --- Endpoints -----------------------------------------------------------

export const api = {
  login(email: string, password: string) {
    // OAuth2PasswordRequestForm expects form-encoded `username`/`password`.
    return apiFetch<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: new URLSearchParams({ username: email, password }),
    });
  },
  register(email: string, password: string) {
    return apiFetch<User>("/auth/register", {
      method: "POST",
      body: { email, password },
    });
  },
  listActivities(limit = 20, offset = 0) {
    return apiFetch<ActivityList>(`/activities?limit=${limit}&offset=${offset}`);
  },
  getActivity(id: string) {
    return apiFetch<ActivityDetail>(`/activities/${encodeURIComponent(id)}`);
  },
  getHealthSummary(days = 7) {
    // Bucket days in the viewer's timezone so overnight sleep lands on the local date.
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
    return apiFetch<HealthSummary>(
      `/health-summary?days=${days}&tz=${encodeURIComponent(tz)}`,
    );
  },
  logWorkout(input: { text?: string; file?: File }) {
    const form = new FormData();
    if (input.text) form.append("text", input.text);
    if (input.file) form.append("file", input.file);
    return apiFetch<WorkoutSubmission>("/workouts/manual", { method: "POST", body: form });
  },
  getHuaweiAuthorizeUrl() {
    return apiFetch<{ url: string }>("/auth/huawei/authorize-url");
  },
};
