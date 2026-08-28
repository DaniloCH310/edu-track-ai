import { request } from "./api.js";
import { qs, empty, escapeHtml, formatDate, loading, errorState } from "./ui.js";

export async function renderDashboard() {
  const metrics = qs("#metrics-grid"), progress = qs("#subject-progress"), upcoming = qs("#upcoming-tasks");
  metrics.innerHTML = '<div class="metric"><span>Carregando...</span></div>'; loading(progress); loading(upcoming);
  try {
    const data = await request("/dashboard");
    const cards = [
      ["Progresso geral", `${data.overall_progress}%`, `${data.completed_tasks} de ${data.total_tasks} tarefas`, "var(--primary-soft)"],
      ["Disciplinas", data.total_subjects, "frentes de estudo", "var(--success-soft)"],
      ["Próximos 3 dias", data.due_soon, "entregas no radar", "var(--warning-soft)"],
      ["Em atraso", data.overdue, data.overdue ? "pedem sua atenção" : "tudo em dia", "var(--danger-soft)"],
    ];
    metrics.innerHTML = cards.map(([label, value, note, color]) => `<article class="metric" style="--metric-color:${color}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join("");
    if (!data.progress_by_subject.length) empty(progress, { symbol: "▤", title: "Nenhuma disciplina ainda", message: "Crie sua primeira disciplina para acompanhar o progresso." });
    else progress.innerHTML = `<div class="progress-list">${data.progress_by_subject.map(item => `<article class="progress-row"><header><strong>${escapeHtml(item.subject_name)}</strong><span>${item.completed_tasks}/${item.total_tasks} tarefas · ${item.progress}%</span></header><div class="progress-track" role="progressbar" aria-label="Progresso de ${escapeHtml(item.subject_name)}" aria-valuenow="${item.progress}" aria-valuemin="0" aria-valuemax="100"><div class="progress-fill" style="--bar-color:${item.color};width:${item.progress}%"></div></div></article>`).join("")}</div>`;
    if (!data.upcoming.length) empty(upcoming, { symbol: "✓", title: "Agenda tranquila", message: "Não há entregas pendentes no momento." });
    else upcoming.innerHTML = `<div class="upcoming-list">${data.upcoming.map(item => `<article class="upcoming-item"><span class="upcoming-dot" style="--dot-color:var(--primary)"></span><p>${escapeHtml(item.title)}<small>${escapeHtml(item.subject_name)}</small></p><span class="upcoming-date">${formatDate(item.due_date)}</span></article>`).join("")}</div>`;
  } catch { errorState(progress, renderDashboard); errorState(upcoming, renderDashboard); metrics.innerHTML = ""; }
}
