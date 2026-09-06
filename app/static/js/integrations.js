import { request } from "./api.js?v=20260906-campus2";
import { confirmAction, errorState, escapeHtml, loading, qs, toast } from "./ui.js?v=20260906-campus2";

const callbackMessages = {
  connected: ["Google Classroom conectado.", "success"],
  access_denied: ["A conexão foi cancelada no Google.", "error"],
  invalid_state: ["A tentativa de conexão expirou. Tente novamente.", "error"],
  access_blocked: ["Sua instituição bloqueou o acesso solicitado.", "error"],
  failed: ["Não foi possível concluir a conexão.", "error"],
};

function consumeCallbackMessage() {
  const url = new URL(location.href);
  const result = url.searchParams.get("classroom");
  if (!result || !callbackMessages[result]) return;
  toast(...callbackMessages[result]);
  url.searchParams.delete("classroom");
  history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

function formatSyncDate(value) {
  if (!value) return "Ainda não sincronizado";
  return `Sincronizado em ${new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))}`;
}

function shell(content, tone = "") {
  return `<section class="integration-bridge surface ${tone}"><div class="integration-bridge__visual" aria-hidden="true"><span class="bridge-node is-edutrack">E</span><i class="bridge-line"><b></b></i><span class="bridge-node is-google"><i class="ph ph-google-logo"></i></span></div>${content}</section>`;
}

function unavailableMarkup() {
  return shell(`<div class="integration-copy"><p class="date-label">CONEXÃO INDISPONÍVEL</p><h2>Google Classroom</h2><p>O administrador do EduTrack ainda precisa configurar esta ponte.</p><small>Suas disciplinas e tarefas locais continuam funcionando normalmente.</small></div>`, "is-muted");
}

function disconnectedMarkup() {
  return shell(`<div class="integration-copy"><span class="integration-status is-ready"><i class="ph ph-shield-check"></i>Importação somente leitura</span><p class="date-label">NOVA PONTE</p><h2>Google Classroom</h2><p>Traga disciplinas e atividades com prazo para o seu campus. O EduTrack não altera nem entrega trabalhos no Google.</p><ul><li><i class="ph ph-check"></i>Seus tokens ficam protegidos no servidor</li><li><i class="ph ph-check"></i>A sincronização acontece quando você solicitar</li><li><i class="ph ph-check"></i>Dados importados permanecem após desconectar</li></ul></div><div class="integration-actions"><button class="button button--primary" id="connect-classroom" type="button"><i class="ph ph-google-logo"></i>Conectar Google Classroom</button><small>Você será direcionado ao Google.</small></div>`);
}

function connectedMarkup(status, result = null) {
  const summary = result ? `<div class="sync-result"><strong>Sincronização concluída</strong><div><span><b>${result.courses_created}</b> disciplinas novas</span><span><b>${result.courses_updated}</b> disciplinas atualizadas</span><span><b>${result.tasks_created}</b> tarefas novas</span><span><b>${result.tasks_updated}</b> tarefas atualizadas</span><span><b>${result.skipped_without_due_date}</b> sem prazo ignoradas</span></div></div>` : "";
  const attention = status.last_error_code ? "is-attention" : "is-connected";
  return shell(`<div class="integration-copy"><span class="integration-status ${attention}"><i class="ph ${status.last_error_code ? "ph-warning" : "ph-check-circle"}"></i>${status.last_error_code ? "Ação necessária" : "Conectado"}</span><p class="date-label">PONTE ATIVA</p><h2>Google Classroom</h2><p>${status.last_error_code ? "A última tentativa falhou. Sincronize novamente; se persistir, reconecte sua conta." : "Suas atividades podem atravessar esta ponte e virar missões no campus."}</p><small>${escapeHtml(formatSyncDate(status.last_synced_at))}</small>${summary}</div><div class="integration-actions"><button class="button button--primary" id="sync-classroom" type="button"><i class="ph ph-arrows-clockwise"></i>Sincronizar agora</button><button class="button button--ghost" id="disconnect-classroom" type="button">Desconectar</button></div>`, status.last_error_code ? "has-warning" : "");
}

function bindDisconnected(container) {
  container.querySelector("#connect-classroom")?.addEventListener("click", () => {
    location.assign("/api/integrations/classroom/authorize");
  });
}

function bindConnected(container, status) {
  container.querySelector("#sync-classroom")?.addEventListener("click", async event => {
    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = '<i class="ph ph-spinner"></i>Sincronizando...';
    try {
      const result = await request("/integrations/classroom/sync", { method: "POST" });
      const fresh = await request("/integrations/classroom");
      container.innerHTML = connectedMarkup(fresh, result);
      bindConnected(container, fresh);
      toast("Sincronização concluída.");
    } catch (error) {
      toast(error.message, "error");
      await renderIntegrations();
    }
  });
  container.querySelector("#disconnect-classroom")?.addEventListener("click", async () => {
    const confirmed = await confirmAction("Desconectar Google Classroom?", "As disciplinas e tarefas importadas continuarão no EduTrack.");
    if (!confirmed) return;
    await request("/integrations/classroom/connection", { method: "DELETE" });
    toast("Google Classroom desconectado.");
    await renderIntegrations();
  });
}

export async function renderIntegrations() {
  const container = qs("#classroom-integration");
  consumeCallbackMessage();
  loading(container);
  try {
    const status = await request("/integrations/classroom");
    if (!status.available) {
      container.innerHTML = unavailableMarkup();
      return;
    }
    if (!status.connected) {
      container.innerHTML = disconnectedMarkup();
      bindDisconnected(container);
      return;
    }
    container.innerHTML = connectedMarkup(status);
    bindConnected(container, status);
  } catch {
    errorState(container, renderIntegrations);
  }
}
