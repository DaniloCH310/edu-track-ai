import { request } from "./api.js?v=20260910-edu-ia1";
import { initAuth, loadCurrentUser, resetAuthView } from "./auth.js?v=20260910-edu-ia1";
import { renderDashboard } from "./dashboard.js?v=20260910-edu-ia1";
import { renderEduIA, openEduIAContext } from "./edu-ia.js?v=20260910-chat3";
import { renderIntegrations } from "./integrations.js?v=20260910-edu-ia1";
import { changeAgendaWeek, renderAgenda, resetAgendaWeek } from "./agenda.js?v=20260910-edu-ia1";
import { setUser, state } from "./state.js?v=20260910-edu-ia1";
import { loadSubjects, openSubjectForm, renderSubjects, submitSubject } from "./subjects.js?v=20260910-edu-ia1";
import { openTaskForm, renderTasks, submitTask } from "./tasks.js?v=20260910-edu-ia1";
import { bindDialogControls, initPasswordToggles, initTheme, qs, qsa, toast } from "./ui.js?v=20260910-edu-ia1";

const routes = { dashboard: renderDashboard, agenda: renderAgenda, subjects: renderSubjects, tasks: renderTasks, "edu-ia": renderEduIA, integrations: renderIntegrations };
const routeTitles = { dashboard: "Dashboard", agenda: "Agenda", subjects: "Disciplinas", tasks: "Tarefas", "edu-ia": "EDU IA", integrations: "Integrações" };

function showAuth(reset = true) { setUser(null); qs("#app-shell").hidden = true; qs("#auth-view").hidden = false; if (reset) resetAuthView(); document.title = "EduTrack AI — Entrar"; }
async function showApp(user) {
  setUser(user); qs("#auth-view").hidden = true; qs("#app-shell").hidden = false;
  qs("#user-name").textContent = user.name; qs("#user-email").textContent = user.email; qs("#user-avatar").textContent = user.name.trim().charAt(0).toUpperCase(); qs("#greeting").textContent = `Olá, ${user.name.split(" ")[0]}`;
  qs("#today-label").textContent = new Intl.DateTimeFormat("pt-BR", { weekday: "long", day: "2-digit", month: "long" }).format(new Date()).toUpperCase();
  try { await loadSubjects(); } catch { toast("Não foi possível carregar as disciplinas.", "error"); }
  await navigate();
}
async function navigate() { if (!state.user) return; const route = location.hash.replace("#", "") || "dashboard"; state.route = routes[route] ? route : "dashboard"; qsa("[data-view]").forEach(view => view.hidden = view.dataset.view !== state.route); qsa("[data-route]").forEach(link => link.classList.toggle("is-active", link.dataset.route === state.route)); qs(".sidebar").classList.remove("is-open"); qs("#mobile-menu-button").setAttribute("aria-expanded", "false"); document.title = `${routeTitles[state.route]} — EduTrack AI`; await routes[state.route](); }

document.addEventListener("DOMContentLoaded", async () => {
  initTheme(); initPasswordToggles(); bindDialogControls(); initAuth(showApp);
  qs("#entity-form").addEventListener("submit", event => { event.preventDefault(); event.currentTarget.dataset.kind === "subject" ? submitSubject(event.currentTarget) : submitTask(event.currentTarget); });
  qs("#new-subject-button").addEventListener("click", () => openSubjectForm()); qsa("#new-task-button,[data-new-task]").forEach(button => button.addEventListener("click", () => openTaskForm()));
  qs("#logout-button").addEventListener("click", async () => { try { await request("/auth/logout", { method: "POST" }); } finally { showAuth(); location.hash = ""; toast("Sessão encerrada."); } });
  qs("#mobile-menu-button").addEventListener("click", event => { const open = qs(".sidebar").classList.toggle("is-open"); event.currentTarget.setAttribute("aria-expanded", String(open)); });
  qs("#agenda-previous").addEventListener("click", () => changeAgendaWeek(-1)); qs("#agenda-current").addEventListener("click", resetAgendaWeek); qs("#agenda-next").addEventListener("click", () => changeAgendaWeek(1));
  qs("#edu-ia-new-conversation").addEventListener("click", () => openEduIAContext({}));
  document.addEventListener("click", event => {
    const trigger = event.target.closest("[data-edu-ai-task],[data-edu-ai-subject]");
    if (!trigger) return;
    event.preventDefault();
    openEduIAContext(trigger.dataset.eduAiTask ? { task_id: trigger.dataset.eduAiTask } : { subject_id: trigger.dataset.eduAiSubject });
  });
  let timer; qs("#task-search").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(renderTasks, 250); }); qsa("#task-status-filter,#task-subject-filter,#task-order").forEach(select => select.addEventListener("change", renderTasks));
  window.addEventListener("hashchange", navigate); window.addEventListener("data:changed", () => { if (state.route === "dashboard") renderDashboard(); if (state.route === "agenda") renderAgenda(); }); window.addEventListener("auth:required", () => showAuth());
  try { const user = await loadCurrentUser(); if (user) await showApp(user); else showAuth(!new URLSearchParams(location.search).has("reset_token")); } catch { showAuth(); toast("Não foi possível conectar ao servidor.", "error"); }
});
