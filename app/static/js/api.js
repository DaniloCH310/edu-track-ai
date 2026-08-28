export class ApiError extends Error {
  constructor(code, message, fields = {}, status = 0) {
    super(message); this.name = "ApiError"; this.code = code; this.fields = fields; this.status = status;
  }
}

export async function request(path, options = {}) {
  const config = { credentials: "same-origin", ...options, headers: { ...(options.headers || {}) } };
  if (config.body && typeof config.body !== "string") {
    config.headers["Content-Type"] = "application/json";
    config.body = JSON.stringify(config.body);
  }
  const response = await fetch(`/api${path}`, config);
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = data.error || {};
    if (response.status === 401 && !path.startsWith("/auth/")) window.dispatchEvent(new CustomEvent("auth:required"));
    throw new ApiError(error.code || "request_failed", error.message || "Não foi possível concluir a operação.", error.fields || {}, response.status);
  }
  return data;
}
