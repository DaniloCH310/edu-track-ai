import { request } from "./api.js?v=20260906-campus2";
import { state } from "./state.js?v=20260906-campus2";
import { qs, clearErrors, closeEntityDialog, confirmAction, empty, errorState, escapeHtml, formatDate, loading, setBusy, showErrors, toast } from "./ui.js?v=20260906-campus2";

const labels = { pending: "Pendente", in_progress: "Em andamento", completed: "Concluída" };
const statusIcons = { pending: "ph-flag", in_progress: "ph-play", completed: "ph-check" };
const statusStyle = value => value === "completed" ? "--status-color:var(--success);--status-bg:var(--success-soft)" : value === "in_progress" ? "--status-color:var(--warning);--status-bg:var(--warning-soft)" : "--status-color:var(--muted);--status-bg:var(--surface-subtle)";
const classroomBadge = source => source === "google_classroom" ? '<span class="classroom-badge"><i class="ph ph-google-logo" aria-hidden="true"></i>Google Classroom</span>' : "";
const classroomLink = task => task.source === "google_classroom" && typeof task.external_url === "string" && task.external_url.startsWith("https://classroom.google.com/") ? `<a class="classroom-link" href="${escapeHtml(task.external_url)}" target="_blank" rel="noopener noreferrer"><i class="ph ph-arrow-square-out" aria-hidden="true"></i>Abrir no Classroom</a>` : "";
const taskFields = task => `<label class="full">Título<input name="title" maxlength="200" required value="${escapeHtml(task?.title || "")}"><small class="field-error" data-error-for="title"></small></label><label>Disciplina<select name="subject_id" required><option value="">Selecione...</option>${state.subjects.map(subject => `<option value="${subject.id}" ${task?.subject_id === subject.id ? "selected" : ""}>${escapeHtml(subject.name)}</option>`).join("")}</select><small class="field-error" data-error-for="subject_id"></small></label><label>Prazo<input name="due_date" type="date" required value="${task?.due_date || ""}"><small class="field-error" data-error-for="due_date"></small></label><label>Status<select name="status"><option value="pending" ${task?.status === "pending" ? "selected" : ""}>Pendente</option><option value="in_progress" ${task?.status === "in_progress" ? "selected" : ""}>Em andamento</option><option value="completed" ${task?.status === "completed" ? "selected" : ""}>Concluída</option></select></label><label class="full">Descrição<textarea name="description" maxlength="4000">${escapeHtml(task?.description || "")}</textarea><small class="field-error" data-error-for="description"></small></label>`;

let taskViewMode = localStorage.getItem("edutrack-tasks-view") === "list" ? "list" : "missions";

function localDate(date = new Date()) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

function daysFromToday(dueDate) {
  const due = new Date(`${dueDate}T12:00:00`);
  const today = new Date(`${localDate()}T12:00:00`);
  return Math.round((due - today) / 86400000);
}

function timingFor(task) {
  if (task.status === "completed") return { key: "completed", label: "Missão concluída", group: "completed" };
  const days = daysFromToday(task.due_date);
  if (days < 0) return { key: "overdue", label: `Atrasada há ${Math.abs(days)} ${Math.abs(days) === 1 ? "dia" : "dias"}`, group: "overdue" };
  if (days === 0) return { key: "today", label: "Entrega hoje", group: "today" };
  if (days <= 7) return { key: "soon", label: `Em ${days} ${days === 1 ? "dia" : "dias"}`, group: "soon" };
  return { key: "later", label: formatDate(task.due_date, { day: "2-digit", month: "short" }), group: "later" };
}

function overviewMarkup(tasks) {
  const overdue = tasks.filter(task => timingFor(task).key === "overdue").length;
  const items = [
    ["ph-list-checks", "Pendentes", tasks.filter(task => task.status === "pending").length, "missões aguardando", "pending"],
    ["ph-lightning", "Em andamento", tasks.filter(task => task.status === "in_progress").length, "foco atual", "active"],
    ["ph-trophy", "Concluídas", tasks.filter(task => task.status === "completed").length, "vitórias registradas", "completed"],
    ["ph-warning", "Em atraso", overdue, overdue ? "pedem atenção" : "tudo no prazo", overdue ? "overdue" : "safe"],
  ];
  return `<section id="tasks-overview" class="tasks-overview" aria-label="Resumo das tarefas">${items.map(([icon, label, value, note, tone]) => `<article class="is-${tone}"><i class="ph ${icon}" aria-hidden="true"></i><div><span>${label}</span><strong>${value}</strong><small>${note}</small></div></article>`).join("")}</section>`;
}

function priorityTask(tasks) {
  return tasks.filter(task => task.status !== "completed").sort((left, right) => {
    const dueOrder = left.due_date.localeCompare(right.due_date);
    if (dueOrder) return dueOrder;
    if (left.status !== right.status) return left.status === "in_progress" ? -1 : 1;
    return left.title.localeCompare(right.title);
  })[0] || null;
}

function priorityMarkup(task) {
  if (!task) return `<section id="task-priority" class="task-priority is-clear surface"><div class="task-priority__icon"><i class="ph ph-confetti" aria-hidden="true"></i></div><div><p class="date-label">ROTA CONCLUÍDA</p><h2>Campus em dia</h2><p>Suas missões foram concluídas. Aproveite para revisar o conteúdo ou planejar o próximo passo.</p></div><button class="button button--primary" type="button" data-new-task>Planejar nova missão</button></section>`;
  const timing = timingFor(task);
  const action = task.status === "pending" ? `<button class="button button--primary" type="button" data-start-task="${task.id}">Começar missão</button>` : `<button class="button button--primary" type="button" data-edit-task="${task.id}">Continuar missão</button>`;
  return `<section id="task-priority" class="task-priority is-${timing.key} surface"><div class="task-priority__icon"><i class="ph ph-navigation-arrow" aria-hidden="true"></i></div><div class="task-priority__copy"><p class="date-label">PRÓXIMO PASSO RECOMENDADO</p><h2>Missão prioritária</h2><h3>${escapeHtml(task.title)}</h3><p><strong>${escapeHtml(task.subject_name || "Sem disciplina")}</strong> · ${timing.label.toLowerCase()}</p><small>${escapeHtml(task.description || "Conclua esta entrega para fazer seu campus avançar.")}</small></div><div class="task-priority__actions"><span class="task-deadline is-${timing.key}"><i class="ph ph-calendar" aria-hidden="true"></i>${formatDate(task.due_date, { day: "2-digit", month: "long" })}</span>${action}</div></section>`;
}

function statusControl(task) {
  return `<select class="status-select" style="${statusStyle(task.status)}" data-task-status="${task.id}" aria-label="Status de ${escapeHtml(task.title)}">${Object.entries(labels).map(([value, label]) => `<option value="${value}" ${value === task.status ? "selected" : ""}>${label}</option>`).join("")}</select>`;
}

function eduIAButton(task) {
  return `<button class="action-button" type="button" data-edu-ai-task="${task.id}" aria-label="Tirar dúvida com EDU IA sobre ${escapeHtml(task.title)}"><i class="ph ph-sparkle" aria-hidden="true"></i></button>`;
}

function missionCard(task) {
  const timing = timingFor(task);
  return `<article class="task-mission-card is-${timing.key}"><header><span class="task-mission-card__state"><i class="ph ${statusIcons[task.status]}" aria-hidden="true"></i></span><span class="task-deadline is-${timing.key}">${timing.label}</span></header><div class="task-mission-card__copy"><p>${escapeHtml(task.subject_name || "Sem disciplina")}</p>${classroomBadge(task.source)}<h3>${escapeHtml(task.title)}</h3><small>${escapeHtml(task.description || "Sem descrição adicional.")}</small>${classroomLink(task)}</div><footer><div>${statusControl(task)}</div><div class="row-actions">${eduIAButton(task)}<button class="action-button" type="button" data-edit-task="${task.id}" aria-label="Editar ${escapeHtml(task.title)}"><i class="ph ph-pencil-simple" aria-hidden="true"></i></button><button class="action-button danger" type="button" data-delete-task="${task.id}" aria-label="Excluir ${escapeHtml(task.title)}"><i class="ph ph-trash" aria-hidden="true"></i></button></div></footer></article>`;
}

function missionBoardMarkup(tasks) {
  const definitions = [
    ["overdue", "Atenção imediata", "Prazos que já venceram", "ph-warning"],
    ["today", "Missões de hoje", "Entregas para concluir agora", "ph-sun"],
    ["soon", "Próximos 7 dias", "Prepare o caminho com antecedência", "ph-calendar-dots"],
    ["later", "Mais adiante", "Missões que estão no horizonte", "ph-binoculars"],
    ["completed", "Concluídas", "Resultados já conquistados", "ph-trophy"],
  ];
  const groups = definitions.map(([key, title, note, icon]) => {
    const grouped = tasks.filter(task => timingFor(task).group === key);
    if (!grouped.length) return "";
    return `<section class="task-mission-group is-${key}"><header><div><i class="ph ${icon}" aria-hidden="true"></i><span><h3>${title}</h3><small>${note}</small></span></div><b>${grouped.length}</b></header><div class="task-mission-group__grid">${grouped.map(missionCard).join("")}</div></section>`;
  }).join("");
  return `<section id="task-mission-board" class="task-mission-board" ${taskViewMode === "missions" ? "" : "hidden"}>${groups}</section>`;
}

function listMarkup(tasks) {
  return `<section id="tasks-list" class="surface content-surface tasks-list" ${taskViewMode === "list" ? "" : "hidden"}><table class="data-table"><thead><tr><th>Tarefa</th><th>Disciplina</th><th>Prazo</th><th>Status</th><th><span class="sr-only">Ações</span></th></tr></thead><tbody>${tasks.map(task => { const timing = timingFor(task); return `<tr><td><strong>${escapeHtml(task.title)}</strong>${classroomBadge(task.source)}<small>${escapeHtml(task.description || "Sem descrição")}</small>${classroomLink(task)}</td><td>${escapeHtml(task.subject_name || "—")}</td><td><span class="task-deadline is-${timing.key}">${formatDate(task.due_date, { day: "2-digit", month: "2-digit", year: "numeric" })}</span></td><td><span class="task-list-status is-${task.status}"><i class="ph ${statusIcons[task.status]}" aria-hidden="true"></i>${labels[task.status]}</span></td><td><div class="row-actions"><button class="action-button" type="button" data-edit-task="${task.id}" aria-label="Editar ${escapeHtml(task.title)}"><i class="ph ph-pencil-simple" aria-hidden="true"></i></button><button class="action-button danger" type="button" data-delete-task="${task.id}" aria-label="Excluir ${escapeHtml(task.title)}"><i class="ph ph-trash" aria-hidden="true"></i></button></div></td></tr>`; }).join("")}</tbody></table></section>`;
}

function toolbarMarkup(count) {
  return `<div class="tasks-toolbar"><div><p class="date-label">MAPA DE MISSÕES</p><h2>Suas próximas entregas</h2><small>${count} ${count === 1 ? "missão encontrada" : "missões encontradas"}</small></div><div class="tasks-view-controls" role="group" aria-label="Visualização das tarefas"><button type="button" data-task-view="missions" aria-pressed="${taskViewMode === "missions"}"><i class="ph ph-squares-four" aria-hidden="true"></i>Vista por missões</button><button type="button" data-task-view="list" aria-pressed="${taskViewMode === "list"}"><i class="ph ph-list-bullets" aria-hidden="true"></i>Vista em lista</button></div></div>`;
}

function bindTaskActions(container, tasks) {
  container.querySelectorAll("[data-task-view]").forEach(button => button.addEventListener("click", () => {
    taskViewMode = button.dataset.taskView;
    localStorage.setItem("edutrack-tasks-view", taskViewMode);
    container.querySelector("#task-mission-board").hidden = taskViewMode !== "missions";
    container.querySelector("#tasks-list").hidden = taskViewMode !== "list";
    container.querySelectorAll("[data-task-view]").forEach(item => item.setAttribute("aria-pressed", String(item.dataset.taskView === taskViewMode)));
  }));
  container.querySelectorAll("[data-task-status]").forEach(select => select.addEventListener("change", () => changeStatus(select, tasks.find(item => item.id === select.dataset.taskStatus))));
  container.querySelectorAll("[data-edit-task]").forEach(button => button.addEventListener("click", () => openTaskForm(tasks.find(item => item.id === button.dataset.editTask))));
  container.querySelectorAll("[data-delete-task]").forEach(button => button.addEventListener("click", () => deleteTask(tasks.find(item => item.id === button.dataset.deleteTask))));
  container.querySelector("[data-start-task]")?.addEventListener("click", event => startTask(event.currentTarget.dataset.startTask));
  container.querySelector("[data-new-task]")?.addEventListener("click", () => openTaskForm());
}

export async function renderTasks() {
  const container = qs("#tasks-content");
  container.className = "tasks-shell";
  loading(container);
  const params = new URLSearchParams();
  const query = qs("#task-search").value.trim();
  const status = qs("#task-status-filter").value;
  const subjectId = qs("#task-subject-filter").value;
  if (query) params.set("query", query);
  if (status) params.set("status", status);
  if (subjectId) params.set("subject_id", subjectId);
  params.set("order", qs("#task-order").value);
  try {
    const tasks = await request(`/tasks?${params}`);
    const hasFilters = Boolean(query || status || subjectId);
    const allTasks = hasFilters ? await request("/tasks?order=due_asc") : tasks;
    const priority = priorityTask(allTasks);
    container.innerHTML = `${overviewMarkup(allTasks)}${priorityMarkup(priority)}${toolbarMarkup(tasks.length)}`;
    if (!tasks.length) {
      container.insertAdjacentHTML("beforeend", '<section class="surface tasks-empty-slot"><div id="tasks-empty"></div></section>');
      empty(qs("#tasks-empty"), { symbol: "✓", title: hasFilters ? "Nenhuma missão encontrada" : "Sua rota está livre", message: hasFilters ? "Tente ajustar a busca ou os filtros." : "Crie uma tarefa para planejar sua próxima entrega.", action: "Nova tarefa", actionId: "empty-new-task" });
      qs("#empty-new-task")?.addEventListener("click", () => openTaskForm());
      container.querySelector("[data-new-task]")?.addEventListener("click", () => openTaskForm());
    } else {
      container.insertAdjacentHTML("beforeend", `${missionBoardMarkup(tasks)}${listMarkup(tasks)}`);
      bindTaskActions(container, tasks);
    }
  } catch {
    container.className = "tasks-shell surface";
    errorState(container, renderTasks);
  }
}

export function openTaskForm(task = null) {
  if (!state.subjects.length) {
    toast("Crie uma disciplina antes da primeira tarefa.", "error");
    location.hash = "subjects";
    return;
  }
  const form = qs("#entity-form");
  qs("#modal-kicker").textContent = task ? "ATUALIZAR TAREFA" : "NOVA TAREFA";
  qs("#modal-title").textContent = task ? "Editar tarefa" : "Planeje uma entrega";
  qs("#modal-fields").innerHTML = taskFields(task);
  form.dataset.kind = "task";
  form.dataset.id = task?.id || "";
  qs("#entity-dialog").showModal();
  form.elements.title.focus();
}

export async function submitTask(form) {
  clearErrors(form);
  setBusy(form, true);
  const raw = Object.fromEntries(new FormData(form));
  const body = { ...raw, description: raw.description || null };
  try {
    await request(form.dataset.id ? `/tasks/${form.dataset.id}` : "/tasks", { method: form.dataset.id ? "PUT" : "POST", body });
    closeEntityDialog();
    toast(form.dataset.id ? "Tarefa atualizada." : "Tarefa criada.");
    await renderTasks();
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    showErrors(form, error.fields);
    if (!Object.keys(error.fields || {}).length) toast(error.message, "error");
  } finally {
    setBusy(form, false);
  }
}

async function startTask(taskId) {
  try {
    await request(`/tasks/${taskId}/status`, { method: "PATCH", body: { status: "in_progress" } });
    toast("Missão iniciada.");
    await renderTasks();
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    toast(error.message, "error");
  }
}

async function changeStatus(select, task) {
  const previous = task.status;
  select.disabled = true;
  try {
    await request(`/tasks/${task.id}/status`, { method: "PATCH", body: { status: select.value } });
    toast("Status atualizado.");
    await renderTasks();
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    select.value = previous;
    toast(error.message, "error");
  } finally {
    select.disabled = false;
  }
}

async function deleteTask(task) {
  if (!await confirmAction("Excluir tarefa?", `“${task.title}” será removida permanentemente.`)) return;
  try {
    await request(`/tasks/${task.id}`, { method: "DELETE" });
    toast("Tarefa excluída.");
    await renderTasks();
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    toast(error.message, "error");
  }
}
