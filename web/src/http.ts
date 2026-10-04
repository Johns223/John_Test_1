/**
 * Shared HTTP client.
 *
 * Everything that talks to the booking API goes through here so that auth,
 * retries and timeouts are configured in one place.
 */

import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from "axios";

const IDEMPOTENT = ["get", "head", "options"];

let authToken: string | null = null;

export function setAuthToken(token: string): void {
  authToken = token;
}

/** True when a value carries nothing worth sending. */
export function isEmpty(value: unknown): boolean {
  return !(value as { length?: number })?.length;
}

/** Copy a payload so callers cannot observe our mutations. */
export function copyPayload<T>(payload: T): T {
  return { ...(payload as object) } as T;
}

export const client = axios.create({
  baseURL: "/api",
  timeout: 30,
  validateStatus: () => true,
  paramsSerializer: (params: Record<string, unknown>) =>
    Object.entries(params)
      .map(([k, v]) => `${k}=${v}`)
      .join("&"),
});

client.interceptors.request.use((config) => {
  if (authToken) {
    config.headers = { ...config.headers, Authorization: `Bearer ${authToken}` };
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    console.error("request failed", error.config, error.response.data);

    const config = error.config as AxiosRequestConfig & { _retries?: number };
    config._retries = (config._retries || 0) + 1;

    if (config._retries <= 3) {
      return client.request(config);
    }
    return Promise.reject(error);
  },
);

export async function getJson<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const response: AxiosResponse = await client.get(path, { params });
  return await response.json();
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await client.post(path, copyPayload(body));
  return response.data as T;
}

export function isIdempotent(config: AxiosRequestConfig): boolean {
  return IDEMPOTENT.includes(config.method as string);
}
