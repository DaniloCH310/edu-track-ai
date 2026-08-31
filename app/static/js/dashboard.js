import { request } from "./api.js";
import { qs, empty, escapeHtml, formatDate, loading, errorState } from "./ui.js";

const metricIcons = ["ph-chart-bar", "ph-book-open", "ph-calendar-dots", "ph-clock"];
const journeySlots = ["completed", "current", "next"];

function statusFor(subject) {
  if (subject.progress >= 100) return "completed";
  if (subject.progress > 0) return "current";
  return "next";
}

function journeyLevel(progress) {
  const level = Math.max(1, Math.min(4, Math.ceil(progress / 25)));
  const stars = Math.max(1, Math.min(3, Math.ceil(progress / 34)));
  return `<span>Nível ${level}</span><span class="journey-stars" aria-label="${stars} de 3 estrelas">${[1, 2, 3].map(index => `<i class="${index <= stars ? "ph-fill" : "ph"} ph-star${index <= stars ? " star--earned" : ""}" aria-hidden="true"></i>`).join("")}</span>`;
}

function nextDueDate(subjectName, upcoming) {
  const task = upcoming.find(item => item.subject_name === subjectName);
  return task ? formatDate(task.due_date, { day: "2-digit", month: "short" }) : "Sem prazo pendente";
}

function journeyMarkup(subjects, upcoming) {
  const ordered = [...subjects].sort((left, right) => right.progress - left.progress).slice(0, 3);
  const usedSlots = new Set();
  return ordered.map((subject, index) => {
    const state = statusFor(subject);
    const preferredSlot = { completed: "completed", current: "current", next: "next" }[state];
    const slot = !usedSlots.has(preferredSlot) ? preferredSlot : journeySlots.find(item => !usedSlots.has(item)) || journeySlots[index];
    usedSlots.add(slot);
    const taskCopy = subject.total_tasks === 1 ? "tarefa" : "tarefas";
    return `<button class="journey-stop journey-stop--${slot} is-${state}" type="button" aria-label="Explorar ${escapeHtml(subject.subject_name)}" aria-expanded="false">
      <span class="journey-stop-label"><strong>${escapeHtml(subject.subject_name)}</strong><small>${state === "completed" ? "Concluído" : state === "current" ? "Em andamento" : "Próxima etapa"}</small></span>
      <span class="journey-tooltip" role="tooltip">
        <strong>${escapeHtml(subject.subject_name)}</strong>
        <span class="tooltip-progress"><span style="width:${subject.progress}%"></span></span>
        <span><b>${subject.progress}%</b> concluído</span>
        <span>${subject.completed_tasks} de ${subject.total_tasks} ${taskCopy}</span>
        <span>Próximo prazo: <b>${escapeHtml(nextDueDate(subject.subject_name, upcoming))}</b></span>
      </span>
    </button>`;
  }).join("");
}

function bindJourneyStops(container) {
  container.querySelectorAll(".journey-stop").forEach(stop => {
    stop.addEventListener("click", event => {
      const open = event.currentTarget.getAttribute("aria-expanded") !== "true";
      container.querySelectorAll(".journey-stop").forEach(item => item.setAttribute("aria-expanded", "false"));
      event.currentTarget.setAttribute("aria-expanded", String(open));
    });
  });
}

function renderLegend() {
  qs("#journey-legend").innerHTML = `
    <span><i class="legend-dot is-completed"></i>Concluído</span>
    <span><i class="legend-dot is-current"></i>Em andamento</span>
    <span><i class="legend-dot is-next"></i>Próxima etapa</span>
    <span><i class="legend-dot is-locked"></i>Bloqueado</span>`;
}

function renderStudyPlan(recommendation) {
  let panel = qs("#study-plan");
  if (!panel) {
    panel = document.createElement("section");
    panel.id = "study-plan";
    panel.className = "study-plan surface";
    qs(".dashboard-grid").before(panel);
  }
  if (!recommendation) {
    panel.innerHTML = '<div class="study-plan__icon" aria-hidden="true"><i class="ph ph-check-circle"></i></div><div><p class="date-label">PLANO DE ESTUDO INTELIGENTE</p><h2>Seu plano está em dia</h2><p>Crie uma tarefa para receber a próxima recomendação de estudo.</p></div><a class="button button--ghost" href="#tasks">Ver tarefas</a>';
    return;
  }
  const priority = recommendation.priority === "urgent" ? "Urgente" : recommendation.priority === "attention" ? "Atenção" : "Próximo passo";
  panel.innerHTML = `<div class="study-plan__icon is-${recommendation.priority}" aria-hidden="true"><i class="ph ph-sparkle"></i></div><div class="study-plan__copy"><p class="date-label">PLANO DE ESTUDO INTELIGENTE</p><h2>${escapeHtml(recommendation.title)}</h2><p><strong>${escapeHtml(recommendation.subject_name)}</strong> · prazo ${formatDate(recommendation.due_date, { day: "2-digit", month: "long" })}</p><small>${escapeHtml(recommendation.reason)}</small></div><div class="study-plan__action"><span class="study-plan__priority is-${recommendation.priority}">${priority}</span><a class="button button--ghost" href="#agenda">Abrir agenda</a></div>`;
}

export async function renderDashboard() {
  const metrics = qs("#metrics-grid");
  const progress = qs("#subject-progress");
  const upcoming = qs("#upcoming-tasks");
  metrics.innerHTML = '<div class="metric"><span>Carregando...</span></div>';
  loading(progress);
  loading(upcoming);
  renderLegend();
  try {
    const data = await request("/dashboard");
    renderStudyPlan(data.recommended_task);
    const cards = [
      ["Progresso geral", `${data.overall_progress}%`, `${data.completed_tasks} de ${data.total_tasks} tarefas`, "var(--primary-soft)"],
      ["Disciplinas", data.total_subjects, "frentes de estudo", "var(--success-soft)"],
      ["Próximos 3 dias", data.due_soon, "entregas no radar", "var(--warning-soft)"],
      ["Em atraso", data.overdue, data.overdue ? "pedem sua atenção" : "tudo em dia", "var(--danger-soft)"],
    ];
    metrics.innerHTML = cards.map(([label, value, note, color], index) => `<article class="metric" style="--metric-color:${color}"><i class="ph ${metricIcons[index]} metric-icon" aria-hidden="true"></i><div><span>${label}</span><strong>${value}</strong><small>${note}</small></div></article>`).join("");
    qs("#journey-level").innerHTML = journeyLevel(data.overall_progress);
    if (!data.progress_by_subject.length) {
      empty(progress, { title: "Sua jornada começa aqui", message: "Crie uma disciplina para desbloquear a primeira ilha.", action: "Criar disciplina", actionId: "journey-new-subject" });
      qs("#journey-new-subject")?.addEventListener("click", () => { location.hash = "subjects"; });
    } else {
      progress.innerHTML = journeyMarkup(data.progress_by_subject, data.upcoming);
      bindJourneyStops(progress);
    }
    if (!data.upcoming.length) {
      upcoming.innerHTML = '<div class="agenda-empty"><img src="/static/assets/agenda-clear.png" alt="Calendário com tarefa concluída"><h2>Agenda tranquila</h2><p>Não há entregas pendentes no momento.</p></div>';
    } else {
      upcoming.innerHTML = `<div class="upcoming-list">${data.upcoming.map(item => `<article class="upcoming-item"><span class="upcoming-dot" style="--dot-color:var(--primary)"></span><p>${escapeHtml(item.title)}<small>${escapeHtml(item.subject_name)}</small></p><span class="upcoming-date">${formatDate(item.due_date)}</span></article>`).join("")}</div>`;
    }
  } catch {
    errorState(progress, renderDashboard);
    errorState(upcoming, renderDashboard);
    metrics.innerHTML = "";
  }
}
