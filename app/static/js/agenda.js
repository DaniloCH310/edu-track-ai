import { buildWeeklyReview } from "./weekly-review.js?v=20260930-1";
import { request } from "./api.js?v=20260906-campus2";
import { errorState, escapeHtml, loading, qs, toast } from "./ui.js?v=20260906-campus2";

const labels = { pending: "Pendente", in_progress: "Em andamento", completed: "Concluída" };
const weekdayFormatter = new Intl.DateTimeFormat("pt-BR", { weekday: "short" });
const fullDateFormatter = new Intl.DateTimeFormat("pt-BR", { weekday: "long", day: "2-digit", month: "long" });
let weekStart = startOfWeek(new Date());
let selectedDate = localDate(new Date());

function localDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function startOfWeek(value) {
  const date = new Date(value.getFullYear(), value.getMonth(), value.getDate());
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  return date;
}

function daysOfWeek() {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() + index);
    return date;
  });
}

function isOverdue(task) {
  return task.status !== "completed" && task.due_date < localDate(new Date());
}

function statusControl(task, idPrefix = "agenda") {
  return `<label class="sr-only" for="${idPrefix}-status-${task.id}">Status de ${escapeHtml(task.title)} na agenda</label><select id="${idPrefix}-status-${task.id}" class="agenda-status" data-agenda-status="${task.id}" aria-label="Status de ${escapeHtml(task.title)} na agenda">${Object.entries(labels).map(([value, label]) => `<option value="${value}" ${task.status === value ? "selected" : ""}>${label}</option>`).join("")}</select>`;
}

function taskCard(task) {
  const overdue = isOverdue(task);
  return `<article class="agenda-task${overdue ? " is-overdue" : ""}"><span class="agenda-task__state" aria-hidden="true"><i class="ph ${task.status === "completed" ? "ph-check" : task.status === "in_progress" ? "ph-play" : "ph-flag"}"></i></span><div><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.subject_name || "Sem disciplina")}${overdue ? " · Em atraso" : ""}</small></div>${statusControl(task, "secondary")}</article>`;
}

function renderWeeklySummary(tasks, days) {
  const review = buildWeeklyReview(tasks, days[0]);
  const total = review.planned.length;
  const done = review.planned.filter(task => task.status === "completed").length;
  const progress = total ? Math.round(done / total * 100) : 0;
  const shortDate = key => new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" }).format(new Date(key + "T12:00:00"));
  const taskList = items => items.length ? `<ul>${items.slice(0, 3).map(task => `<li><strong>${escapeHtml(task.title)}</strong><span>${escapeHtml(task.subject_name || "Sem disciplina")} · prazo ${shortDate(task.due_date)}</span></li>`).join("")}</ul>${items.length > 3 ? `<p>Mais ${items.length - 3} na agenda.</p>` : ""}` : "<p>Nenhuma entrega deste período está em aberto.</p>";
  let summary = qs("#weekly-summary");
  if (!summary) {
    summary = document.createElement("section");
    summary.id = "weekly-summary";
    summary.setAttribute("aria-labelledby", "weekly-review-title");
    qs(".agenda-surface").before(summary);
  }
  summary.className = "weekly-summary surface";
  const subtitle = review.future
    ? "Uma visão das entregas previstas para este período."
    : review.historical
      ? "Conclusões registradas no período e pendências conforme o status atual."
      : "A semana ainda está em andamento. Este fechamento acompanha suas atualizações.";
  summary.innerHTML = `<div class="weekly-summary__icon" aria-hidden="true"><i class="ph ph-calendar-check"></i></div>
    <div class="weekly-summary__copy"><p class="date-label">${review.future ? "PLANEJAMENTO SEMANAL" : "FECHAMENTO SEMANAL"} · ${shortDate(review.first)} a ${shortDate(review.last)}</p><h2 id="weekly-review-title">${done} de ${total} tarefas com prazo nesta semana estão concluídas</h2><p>${subtitle}</p></div>
    <div class="weekly-summary__progress"><strong>${progress}%</strong><span class="weekly-progress-track" role="progressbar" aria-label="Tarefas concluídas entre as previstas para a semana" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><i style="width:${progress}%"></i></span></div>
    <div class="weekly-review-grid">
      <section><h3>O que avançou</h3><p>${review.completed.length ? `${review.completed.length} ${review.completed.length === 1 ? "tarefa concluída" : "tarefas concluídas"} entre ${shortDate(review.first)} e ${shortDate(review.last)}, independentemente do prazo.` : review.future ? "As conclusões registradas neste período aparecerão aqui." : "Não há conclusões registradas neste período. Isso não mede todo o seu esforço."}</p>
      ${review.groups.length ? `<ul>${review.groups.map(group => `<li><strong>${escapeHtml(group.name)}</strong><span>${group.count} ${group.count === 1 ? "conclusão" : "conclusões"}</span></li>`).join("")}</ul>` : ""}
      </section>
      <section><h3>${review.future ? "O que está previsto" : "O que segue em aberto"}</h3>${taskList(review.pending)}
      ${review.backlog.length ? `<p>${review.backlog.length} ${review.backlog.length === 1 ? "pendência anterior também pode" : "pendências anteriores também podem"} entrar no próximo planejamento.</p>` : ""}
      </section>
      <section><h3>Uma proposta para a próxima semana</h3><p>${shortDate(review.nextDays[0])} a ${shortDate(review.nextDays[6])} · ${review.upcoming.length} entregas já previstas.</p>
      ${review.proposal.length ? `<ol>${review.proposal.map(item => `<li><strong>${shortDate(item.day)} · ${item.minutes} min para ${escapeHtml(item.task.title)}</strong><span>${item.overdue ? "Retomar uma etapa e conferir se o prazo precisa ser combinado." : "Reservar um primeiro bloco antes da entrega."}</span></li>`).join("")}</ol><p>São blocos iniciais, não uma estimativa de conclusão. Ajuste ao tempo que você tem; os prazos permanecem os mesmos.</p>` : "<p>Sem entregas abertas até o fim da próxima semana. Você pode reservar um bloco leve de revisão ou deixar espaço para descansar.</p>"}
      <button type="button" class="button button--ghost" data-review-next-week>Ver próxima semana</button>
      </section>
    </div>`;
  summary.querySelector("[data-review-next-week]").addEventListener("click", () => changeAgendaWeek(1));
}

function normalizeSelectedDay(days, tasks) {
  const keys = days.map(localDate);
  if (keys.includes(selectedDate)) return;
  const firstTaskDay = keys.find(key => tasks.some(task => task.due_date === key));
  selectedDate = firstTaskDay || keys[0];
}

function routeMarkup(days, tasks) {
  const completed = tasks.filter(task => task.status === "completed").length;
  const progress = tasks.length ? Math.round((completed / tasks.length) * 100) : 0;
  return `<nav id="weekly-route" class="weekly-route" aria-label="Rota da semana"><div class="weekly-route__progress" role="progressbar" aria-label="Caminho concluído na semana" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><span style="width:${progress}%"></span></div><div class="weekly-route__days">${days.map(day => {
    const key = localDate(day);
    const dayTasks = tasks.filter(task => task.due_date === key);
    const complete = dayTasks.length > 0 && dayTasks.every(task => task.status === "completed");
    const alert = dayTasks.some(isOverdue);
    const today = key === localDate(new Date());
    const countLabel = `${dayTasks.length} ${dayTasks.length === 1 ? "missão" : "missões"}`;
    return `<button class="weekly-route__day${today ? " is-today" : ""}${complete ? " is-complete" : ""}${alert ? " is-alert" : ""}" type="button" data-route-date="${key}" aria-pressed="${key === selectedDate}" aria-label="${escapeHtml(fullDateFormatter.format(day))}, ${countLabel}"><span>${weekdayFormatter.format(day).replace(".", "")}</span><strong>${String(day.getDate()).padStart(2, "0")}</strong><small>${dayTasks.length ? countLabel : "Dia livre"}</small><i class="ph ${complete ? "ph-check" : alert ? "ph-warning" : dayTasks.length ? "ph-flag" : "ph-circle"}" aria-hidden="true"></i></button>`;
  }).join("")}</div></nav>`;
}

function primaryTask(tasks) {
  return [...tasks].sort((left, right) => {
    const rank = { in_progress: 0, pending: 1, completed: 2 };
    return rank[left.status] - rank[right.status];
  })[0] || null;
}

function missionMarkup(task, day) {
  if (!task) {
    return `<section id="daily-mission" class="daily-mission is-free"><div class="daily-mission__icon" aria-hidden="true"><i class="ph ph-sun-horizon"></i></div><div><p class="date-label">MISSÃO PRINCIPAL</p><h2>Missão principal do dia</h2><h3>Dia livre para reorganizar</h3><p>Use este espaço para revisar conteúdos ou antecipar uma próxima entrega.</p></div><button class="button button--ghost" type="button" data-agenda-new-task>Planejar tarefa</button></section>`;
  }
  const overdue = isOverdue(task);
  const action = task.status === "pending" ? `<button class="button button--primary" type="button" data-start-mission="${task.id}">Começar missão</button>` : task.status === "in_progress" ? `<button class="button button--primary" type="button" data-complete-mission="${task.id}">Concluir missão</button>` : `<span class="mission-complete"><i class="ph-fill ph-check-circle" aria-hidden="true"></i>Missão concluída</span>`;
  return `<section id="daily-mission" class="daily-mission${overdue ? " is-overdue" : ""}"><div class="daily-mission__icon" aria-hidden="true"><i class="ph ${task.status === "completed" ? "ph-trophy" : "ph-navigation-arrow"}"></i></div><div class="daily-mission__copy"><p class="date-label">MISSÃO PRINCIPAL · ${escapeHtml(weekdayFormatter.format(day).replace(".", "").toUpperCase())}</p><h2>Missão principal do dia</h2><h3>${escapeHtml(task.title)}</h3><p><strong>${escapeHtml(task.subject_name || "Sem disciplina")}</strong>${overdue ? " · prazo vencido" : " · entrega de hoje"}</p></div><div class="daily-mission__controls">${statusControl(task, "mission")}${action}</div></section>`;
}

function secondaryMarkup(tasks, primary) {
  const secondary = tasks.filter(task => task.id !== primary?.id);
  return `<section id="agenda-secondary-tasks" class="agenda-secondary"><div class="agenda-section-heading"><div><p class="date-label">DEMAIS ENTREGAS</p><h2>Outras tarefas do dia</h2></div><span>${secondary.length}</span></div>${secondary.length ? `<div class="agenda-secondary__list">${secondary.map(taskCard).join("")}</div>` : '<p class="agenda-secondary__empty">Nenhuma outra entrega neste dia.</p>'}</section>`;
}

function subjectProgressMarkup(progress, weeklyTasks) {
  const subjectIds = new Set(weeklyTasks.map(task => task.subject_id));
  const subjects = progress.filter(subject => subjectIds.has(subject.subject_id));
  return `<section id="agenda-subject-progress" class="agenda-subject-progress"><div class="agenda-campus-preview"><img src="/static/assets/learning-campus.png" alt="Vista do campus de aprendizagem"><span><i class="ph ph-map-pin" aria-hidden="true"></i>Seu campus nesta semana</span></div><div class="agenda-section-heading"><div><p class="date-label">CAMPUS NESTA SEMANA</p><h2>Disciplinas em movimento</h2></div><a href="#dashboard">Ver campus</a></div>${subjects.length ? `<div class="agenda-subject-progress__list">${subjects.map(subject => `<article style="--subject-color:${subject.color}"><i class="ph ph-buildings" aria-hidden="true"></i><div><span><strong>${escapeHtml(subject.subject_name)}</strong><b>${subject.progress}%</b></span><small>${subject.completed_tasks} de ${subject.total_tasks} tarefas</small><span class="agenda-subject-track"><i style="width:${subject.progress}%"></i></span></div></article>`).join("")}</div>` : '<p class="agenda-secondary__empty">As disciplinas com entregas nesta semana aparecerão aqui.</p>'}</section>`;
}

function bindAgendaInteractions(tasks, dashboard) {
  qs("#weekly-route").querySelectorAll("[data-route-date]").forEach(button => button.addEventListener("click", () => {
    selectedDate = button.dataset.routeDate;
    renderWeek(tasks, dashboard);
  }));
  qs("#agenda-content").querySelectorAll("[data-agenda-status]").forEach(select => select.addEventListener("change", () => updateStatus(select, tasks.find(task => task.id === select.dataset.agendaStatus))));
  qs("[data-start-mission]")?.addEventListener("click", event => updateMission(event.currentTarget, tasks.find(task => task.id === event.currentTarget.dataset.startMission), "in_progress"));
  qs("[data-complete-mission]")?.addEventListener("click", event => updateMission(event.currentTarget, tasks.find(task => task.id === event.currentTarget.dataset.completeMission), "completed"));
  qs("[data-agenda-new-task]")?.addEventListener("click", () => qs("[data-new-task]")?.click());
}

function renderWeek(tasks, dashboard) {
  const days = daysOfWeek();
  normalizeSelectedDay(days, tasks);
  renderWeeklySummary(tasks, days);
  const firstDay = localDate(days[0]);
  const lastDay = localDate(days.at(-1));
  const weeklyTasks = tasks.filter(task => task.due_date >= firstDay && task.due_date <= lastDay);
  const dayTasks = weeklyTasks.filter(task => task.due_date === selectedDate);
  const primary = primaryTask(dayTasks);
  const selectedDay = days.find(day => localDate(day) === selectedDate) || days[0];
  const dateFormatter = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" });
  qs("#agenda-range").textContent = `${dateFormatter.format(days[0])} — ${dateFormatter.format(days.at(-1))}`;
  qs("#agenda-content").innerHTML = `${routeMarkup(days, weeklyTasks)}<div class="agenda-day-focus"><div>${missionMarkup(primary, selectedDay)}${secondaryMarkup(dayTasks, primary)}</div>${subjectProgressMarkup(dashboard.progress_by_subject, weeklyTasks)}</div>`;
  bindAgendaInteractions(tasks, dashboard);
}

async function updateStatus(select, task) {
  const previous = task.status;
  select.disabled = true;
  try {
    await request(`/tasks/${task.id}/status`, { method: "PATCH", body: { status: select.value } });
    toast("Status atualizado.");
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    select.value = previous;
    toast(error.message, "error");
  } finally {
    select.disabled = false;
  }
}

async function updateMission(button, task, status) {
  button.disabled = true;
  try {
    await request(`/tasks/${task.id}/status`, { method: "PATCH", body: { status } });
    toast(status === "completed" ? "Missão concluída!" : "Missão iniciada. Bom estudo!");
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    button.disabled = false;
    toast(error.message, "error");
  }
}

export async function renderAgenda() {
  const container = qs("#agenda-content");
  loading(container);
  try {
    const [tasks, dashboard] = await Promise.all([request("/tasks?order=due_asc"), request("/dashboard")]);
    renderWeek(tasks, dashboard);
  } catch {
    errorState(container, renderAgenda);
  }
}

export function changeAgendaWeek(delta) {
  weekStart = new Date(weekStart);
  weekStart.setDate(weekStart.getDate() + (delta * 7));
  selectedDate = localDate(weekStart);
  renderAgenda();
}

export function resetAgendaWeek() {
  weekStart = startOfWeek(new Date());
  selectedDate = localDate(new Date());
  renderAgenda();
}
