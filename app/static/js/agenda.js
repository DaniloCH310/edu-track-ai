import { request } from "./api.js";
import { errorState, escapeHtml, loading, qs, toast } from "./ui.js";

const labels = { pending: "Pendente", in_progress: "Em andamento", completed: "Concluída" };
let weekStart = startOfWeek(new Date());

function localDate(date) { return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }
function startOfWeek(value) { const date = new Date(value.getFullYear(), value.getMonth(), value.getDate()); date.setDate(date.getDate() - ((date.getDay() + 6) % 7)); return date; }
function daysOfWeek() { return Array.from({ length: 7 }, (_, index) => { const date = new Date(weekStart); date.setDate(date.getDate() + index); return date; }); }
function isOverdue(task) { return task.status !== "completed" && task.due_date < localDate(new Date()); }
function taskCard(task) { const overdue = isOverdue(task); return `<article class="agenda-task${overdue ? " is-overdue" : ""}"><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.subject_name || "Sem disciplina")}${overdue ? " · Em atraso" : ""}</small><label class="sr-only" for="agenda-status-${task.id}">Status de ${escapeHtml(task.title)} na agenda</label><select id="agenda-status-${task.id}" class="agenda-status" data-agenda-status="${task.id}" aria-label="Status de ${escapeHtml(task.title)} na agenda">${Object.entries(labels).map(([value, label]) => `<option value="${value}" ${task.status === value ? "selected" : ""}>${label}</option>`).join("")}</select></article>`; }

function renderWeek(tasks) {
  const days = daysOfWeek();
  const dateFormatter = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" });
  qs("#agenda-range").textContent = `${dateFormatter.format(days[0])} — ${dateFormatter.format(days.at(-1))}`;
  qs("#agenda-content").innerHTML = `<div class="agenda-grid">${days.map(day => { const key = localDate(day); const tasksForDay = tasks.filter(task => task.due_date === key); return `<section class="agenda-day${key === localDate(new Date()) ? " is-today" : ""}"><header><span>${new Intl.DateTimeFormat("pt-BR", { weekday: "short" }).format(day).replace(".", "")}</span><strong>${String(day.getDate()).padStart(2, "0")}</strong></header><div class="agenda-day-tasks">${tasksForDay.length ? tasksForDay.map(taskCard).join("") : '<p class="agenda-free">Sem entregas</p>'}</div></section>`; }).join("")}</div>`;
  qs("#agenda-content").querySelectorAll("[data-agenda-status]").forEach(select => select.addEventListener("change", () => updateStatus(select, tasks.find(task => task.id === select.dataset.agendaStatus))));
}

async function updateStatus(select, task) { const previous = task.status; select.disabled = true; try { await request(`/tasks/${task.id}/status`, { method: "PATCH", body: { status: select.value } }); toast("Status atualizado."); window.dispatchEvent(new CustomEvent("data:changed")); } catch (error) { select.value = previous; toast(error.message, "error"); } finally { select.disabled = false; } }
export async function renderAgenda() { const container = qs("#agenda-content"); loading(container); try { renderWeek(await request("/tasks?order=due_asc")); } catch { errorState(container, renderAgenda); } }
export function changeAgendaWeek(delta) { weekStart = new Date(weekStart); weekStart.setDate(weekStart.getDate() + (delta * 7)); renderAgenda(); }
export function resetAgendaWeek() { weekStart = startOfWeek(new Date()); renderAgenda(); }
