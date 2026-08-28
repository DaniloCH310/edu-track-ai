import { request } from "./api.js";
import { qs, qsa, clearErrors, setBusy, showErrors, toast } from "./ui.js";

function switchTab(mode) {
  const login = mode === "login"; qs("#login-form").hidden = !login; qs("#register-form").hidden = login;
  qs("#login-tab").classList.toggle("is-active", login); qs("#register-tab").classList.toggle("is-active", !login);
  qs("#login-tab").setAttribute("aria-selected", String(login)); qs("#register-tab").setAttribute("aria-selected", String(!login));
  qs(login ? "#login-form input" : "#register-form input")?.focus();
}
function showPanel(id) { qsa("#auth-default,#forgot-panel,#reset-panel").forEach(panel => panel.hidden = panel.id !== id); }
export function resetAuthView() { showPanel("auth-default"); switchTab("login"); }
function values(form) { return Object.fromEntries(new FormData(form)); }
function handleFailure(form, error) { showErrors(form, error.fields); if (!Object.keys(error.fields || {}).length) toast(error.message, "error"); }

export function initAuth(onAuthenticated) {
  qs("#login-tab").addEventListener("click", () => switchTab("login")); qs("#register-tab").addEventListener("click", () => switchTab("register"));
  qs("#forgot-link").addEventListener("click", () => showPanel("forgot-panel")); qs("[data-auth-back]").addEventListener("click", () => showPanel("auth-default"));
  const resetToken = new URLSearchParams(location.search).get("reset_token"); if (resetToken) showPanel("reset-panel");
  const bind = (id, path, successMessage) => { const form = qs(id); form.addEventListener("submit", async event => { event.preventDefault(); clearErrors(form); setBusy(form, true); try { const user = await request(path, { method: "POST", body: values(form) }); toast(successMessage); await onAuthenticated(user); } catch (error) { handleFailure(form, error); } finally { setBusy(form, false); } }); };
  bind("#login-form", "/auth/login", "Login realizado com sucesso."); bind("#register-form", "/auth/register", "Sua conta está pronta.");
  qs("#forgot-form").addEventListener("submit", async event => { event.preventDefault(); const form = event.currentTarget; clearErrors(form); setBusy(form, true); try { const result = await request("/auth/forgot-password", { method: "POST", body: values(form) }); toast(result.message); form.reset(); showPanel("auth-default"); } catch (error) { handleFailure(form, error); } finally { setBusy(form, false); } });
  qs("#reset-form").addEventListener("submit", async event => { event.preventDefault(); const form = event.currentTarget; clearErrors(form); setBusy(form, true); try { await request("/auth/reset-password", { method: "POST", body: { token: resetToken, ...values(form) } }); history.replaceState({}, "", location.pathname); toast("Senha redefinida. Você já pode entrar."); form.reset(); showPanel("auth-default"); switchTab("login"); } catch (error) { handleFailure(form, error); } finally { setBusy(form, false); } });
}

export async function loadCurrentUser() { try { return await request("/auth/me"); } catch (error) { if (error.status === 401) return null; throw error; } }
