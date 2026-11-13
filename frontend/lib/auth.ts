/** Auth helpers: session state lives in an httpOnly cookie, never JS storage. */

import { apiGet, ApiError } from "./api";
import type { User } from "@/types";

/** Fetch the signed-in user, or null when the session is missing/expired. */
export async function getCurrentUser(): Promise<User | null> {
  try {
    return await apiGet<User>("/api/auth/me");
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
}

export async function login(email: string, password: string): Promise<User> {
  const { apiPost } = await import("./api");
  return apiPost<User>("/api/auth/login", { email, password });
}

export async function signup(
  email: string,
  password: string,
  name: string
): Promise<User> {
  const { apiPost } = await import("./api");
  return apiPost<User>("/api/auth/signup", { email, password, name });
}

export async function logout(): Promise<void> {
  const { apiPost } = await import("./api");
  await apiPost<void>("/api/auth/logout");
}
