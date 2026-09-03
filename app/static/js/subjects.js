import { request } from "./api.js";
import { setSubjects, state } from "./state.js";
import { qs, clearErrors, closeEntityDialog, confirmAction, empty, errorState, escapeHtml, loading, setBusy, showErrors, toast } from "./ui.js";

const fields = subject => `
  <label class="full">Nome da disciplina<input name="name" required maxlength="160" value="${escapeHtml(subject?.name || "")}"><small class="field-error" data-error-for="name"></small></label>
  <label>Professor<input name="professor" maxlength="160" value="${escapeHtml(subject?.professor || "")}"><small class="field-error" data-error-for="professor"></small></label>
  <label>Carga horária<input name="workload_hours" type="number" min="1" max="10000" required value="${subject?.workload_hours || ""}"><small class="field-error" data-error-for="workload_hours"></small></label>
  <label>Período<input name="period" maxlength="40" placeholder="Ex.: 2026.2" value="${escapeHtml(subject?.period || "")}"><small class="field-error" data-error-for="period"></small></label>
  <label>Cor<input name="color" type="color" value="${subject?.color || "#6750A4"}"><small class="field-error" data-error-for="color"></small></label>
  <label>Data inicial<input name="start_date" type="date" value="${subject?.start_date || ""}"><small class="field-error" data-error-for="start_date"></small></label>
  <label>Data final<input name="end_date" type="date" value="${subject?.end_date || ""}"><small class="field-error" data-error-for="end_date"></small></label>
  <label class="full">Descrição<textarea name="description" maxlength="4000">${escapeHtml(subject?.description || "")}</textarea><small class="field-error" data-error-for="description"></small></label>`;

const buildingZones = ["lab", "library", "studio", "engineering"];
const classroomBadge = source => source === "google_classroom" ? '<span class="classroom-badge"><i class="ph ph-google-logo" aria-hidden="true"></i>Google Classroom</span>' : "";
let subjectsViewMode = localStorage.getItem("edutrack-subjects-view") === "list" ? "list" : "campus";
let selectedSubjectId = null;

function normalizedName(name) {
  return name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function preferredBuilding(name, index) {
  const normalized = normalizedName(name);
  if (/(banco|dados|database|sql)/.test(normalized)) return "library";
  if (/(ux|ui|design|interface)/.test(normalized)) return "studio";
  if (/(algorit|logica|matemat|calculo)/.test(normalized)) return "engineering";
  if (/(python|program|codigo|software)/.test(normalized)) return "lab";
  return buildingZones[index % buildingZones.length];
}

function subjectStatus(stats) {
  if (!stats.total_tasks) return { key: "empty", label: "Sem missões" };
  if (stats.progress >= 100) return { key: "completed", label: "Concluída" };
  if (stats.progress > 0) return { key: "active", label: "Em construção" };
  return { key: "ready", label: "Pronta para começar" };
}

function statsFor(subject, progressMap) {
  return progressMap.get(subject.id) || {
    subject_id: subject.id,
    subject_name: subject.name,
    color: subject.color,
    progress: subject.progress || 0,
    completed_tasks: 0,
    total_tasks: 0,
  };
}

function overviewMarkup(subjects, progressMap) {
  const stats = subjects.map(subject => statsFor(subject, progressMap));
  const completed = stats.filter(item => item.progress >= 100 && item.total_tasks).length;
  const active = stats.filter(item => item.progress > 0 && item.progress < 100).length;
  const withoutTasks = stats.filter(item => !item.total_tasks).length;
  const average = stats.length ? Math.round(stats.reduce((total, item) => total + item.progress, 0) / stats.length) : 0;
  const items = [
    ["ph-buildings", "Disciplinas", subjects.length, "prédios no campus"],
    ["ph-hammer", "Em construção", active, "avançando agora"],
    ["ph-trophy", "Concluídas", completed, "objetivos alcançados"],
    ["ph-chart-line-up", "Progresso médio", `${average}%`, withoutTasks ? `${withoutTasks} sem missões` : "todas em movimento"],
  ];
  return `<section id="subjects-overview" class="subjects-overview" aria-label="Resumo das disciplinas">${items.map(([icon, label, value, note]) => `<article><i class="ph ${icon}" aria-hidden="true"></i><div><span>${label}</span><strong>${value}</strong><small>${note}</small></div></article>`).join("")}</section>`;
}

function focusSubject(subjects, dashboard, progressMap) {
  const recommendedId = dashboard.recommended_task?.subject_id;
  if (recommendedId) return subjects.find(subject => subject.id === recommendedId) || subjects[0];
  return [...subjects].sort((left, right) => {
    const leftStats = statsFor(left, progressMap);
    const rightStats = statsFor(right, progressMap);
    if (Boolean(leftStats.total_tasks) !== Boolean(rightStats.total_tasks)) return rightStats.total_tasks - leftStats.total_tasks;
    return leftStats.progress - rightStats.progress;
  })[0];
}

function focusMarkup(subject, dashboard, stats) {
  const nextTask = dashboard.upcoming.find(task => task.subject_id === subject.id);
  const status = subjectStatus(stats);
  return `<section class="subject-focus" style="--subject-color:${subject.color}"><div class="subject-focus__visual"><img src="/static/assets/learning-campus.png" alt="Prédio em destaque de ${escapeHtml(subject.name)}"><span><i class="ph ph-map-pin" aria-hidden="true"></i>Disciplina em foco</span></div><div class="subject-focus__copy"><p class="date-label">PRÓXIMO DESTINO DO CAMPUS</p><h2>${escapeHtml(subject.name)}</h2><p>${nextTask ? `Sua próxima missão é <strong>${escapeHtml(nextTask.title)}</strong>.` : "Este prédio está pronto para receber uma nova missão."}</p><div class="subject-focus__progress"><span><b>${stats.progress}%</b><small>${status.label}</small></span><i><span style="width:${stats.progress}%"></span></i></div></div><div class="subject-focus__actions"><button class="button button--primary" type="button" data-plan-subject="${subject.id}">${nextTask ? "Planejar próxima missão" : "Criar primeira missão"}</button><button class="button button--ghost" type="button" data-open-subject="${subject.id}">Ver disciplina</button></div></section>`;
}

function buildingCard(subject, stats, index) {
  const zone = preferredBuilding(subject.name, index);
  const status = subjectStatus(stats);
  return `<article class="subject-building is-${status.key}" style="--subject-color:${subject.color}"><button class="subject-building__main" type="button" data-open-subject="${subject.id}" aria-label="Abrir ${escapeHtml(subject.name)}"><span class="subject-building__visual is-${zone}"><img src="/static/assets/learning-campus.png" alt=""><span>${status.label}</span></span><span class="subject-building__copy"><span><strong>${escapeHtml(subject.name)}</strong><b>${stats.progress}%</b></span>${classroomBadge(subject.source)}<small>${escapeHtml(subject.professor || "Professor não informado")} · ${escapeHtml(subject.period || "Período aberto")}</small><span class="subject-building__track"><i style="width:${stats.progress}%"></i></span><em>${stats.completed_tasks} de ${stats.total_tasks} tarefas concluídas</em></span></button><footer><button class="action-button" type="button" data-edit-subject="${subject.id}" aria-label="Editar ${escapeHtml(subject.name)}"><i class="ph ph-pencil-simple" aria-hidden="true"></i></button><button class="action-button danger" type="button" data-delete-subject="${subject.id}" aria-label="Excluir ${escapeHtml(subject.name)}"><i class="ph ph-trash" aria-hidden="true"></i></button></footer></article>`;
}

function campusMarkup(subjects, progressMap) {
  return `<section id="subjects-campus" class="subjects-campus" ${subjectsViewMode === "campus" ? "" : "hidden"}><div class="subjects-campus__intro"><div><p class="date-label">DISTRITO DE DISCIPLINAS</p><h2>Seus prédios de conhecimento</h2></div><p>Cada tarefa concluída fortalece uma área do campus.</p></div><div class="subjects-campus__grid">${subjects.map((subject, index) => buildingCard(subject, statsFor(subject, progressMap), index)).join("")}</div></section>`;
}

function listMarkup(subjects) {
  return `<section id="subjects-list" class="surface content-surface subjects-list" ${subjectsViewMode === "list" ? "" : "hidden"}><table class="data-table"><thead><tr><th>Disciplina</th><th>Professor</th><th>Carga</th><th>Período</th><th>Progresso</th><th><span class="sr-only">Ações</span></th></tr></thead><tbody>${subjects.map(subject => `<tr><td><div class="title-cell"><span class="subject-color" style="--subject-color:${subject.color}"></span><div><strong>${escapeHtml(subject.name)}</strong>${classroomBadge(subject.source)}<small>${escapeHtml(subject.description || "Sem descrição")}</small></div></div></td><td>${escapeHtml(subject.professor || "—")}</td><td>${subject.workload_hours}h</td><td>${escapeHtml(subject.period || "—")}</td><td>${subject.progress}%</td><td><div class="row-actions"><button class="action-button" type="button" data-edit-subject="${subject.id}" aria-label="Editar ${escapeHtml(subject.name)}"><i class="ph ph-pencil-simple" aria-hidden="true"></i></button><button class="action-button danger" type="button" data-delete-subject="${subject.id}" aria-label="Excluir ${escapeHtml(subject.name)}"><i class="ph ph-trash" aria-hidden="true"></i></button></div></td></tr>`).join("")}</tbody></table></section>`;
}

function viewControlsMarkup() {
  return `<div class="subjects-view-controls" role="group" aria-label="Visualização das disciplinas"><button type="button" data-subject-view="campus" aria-pressed="${subjectsViewMode === "campus"}"><i class="ph ph-buildings" aria-hidden="true"></i>Vista do campus</button><button type="button" data-subject-view="list" aria-pressed="${subjectsViewMode === "list"}"><i class="ph ph-list-bullets" aria-hidden="true"></i>Vista em lista</button></div>`;
}

function detailMarkup(subject, stats, dashboard) {
  if (!subject) return "";
  const nextTask = dashboard.upcoming.find(task => task.subject_id === subject.id);
  const status = subjectStatus(stats);
  return `<section id="subject-detail-panel" class="subject-detail-panel" style="--subject-color:${subject.color}" aria-live="polite"><header><div><p class="date-label">DETALHES DO PRÉDIO</p><h2>${escapeHtml(subject.name)}</h2><span class="subject-status is-${status.key}">${status.label}</span></div><button class="icon-button" type="button" data-close-subject aria-label="Fechar detalhes"><i class="ph ph-x" aria-hidden="true"></i></button></header><div class="subject-detail-panel__body"><div class="subject-detail-panel__facts"><span><i class="ph ph-user" aria-hidden="true"></i><small>Professor</small><strong>${escapeHtml(subject.professor || "Não informado")}</strong></span><span><i class="ph ph-clock" aria-hidden="true"></i><small>Carga horária</small><strong>${subject.workload_hours}h</strong></span><span><i class="ph ph-calendar" aria-hidden="true"></i><small>Período</small><strong>${escapeHtml(subject.period || "Aberto")}</strong></span></div><div class="subject-detail-panel__progress"><span><strong>Evolução do prédio</strong><b>${stats.progress}%</b></span><i><span style="width:${stats.progress}%"></span></i><small>${stats.completed_tasks} de ${stats.total_tasks} tarefas concluídas</small></div><div class="subject-detail-panel__mission"><p class="date-label">PRÓXIMA MISSÃO</p><strong>${escapeHtml(nextTask?.title || "Nenhuma missão pendente")}</strong><small>${nextTask ? "Continue avançando por esta disciplina." : "Crie uma tarefa para movimentar este prédio."}</small></div></div><footer><button class="button button--ghost" type="button" data-subject-tasks="${subject.id}">Ver tarefas da disciplina</button><button class="button button--primary" type="button" data-edit-subject="${subject.id}" aria-label="Editar disciplina">Editar disciplina</button></footer></section>`;
}

function bindSubjectActions(container, subjects, dashboard, progressMap) {
  container.querySelectorAll("[data-subject-view]").forEach(button => button.addEventListener("click", () => {
    subjectsViewMode = button.dataset.subjectView;
    localStorage.setItem("edutrack-subjects-view", subjectsViewMode);
    container.querySelector("#subjects-campus").hidden = subjectsViewMode !== "campus";
    container.querySelector("#subjects-list").hidden = subjectsViewMode !== "list";
    container.querySelectorAll("[data-subject-view]").forEach(item => item.setAttribute("aria-pressed", String(item.dataset.subjectView === subjectsViewMode)));
  }));
  container.querySelectorAll("[data-open-subject]").forEach(button => button.addEventListener("click", () => {
    selectedSubjectId = button.dataset.openSubject;
    const subject = subjects.find(item => item.id === selectedSubjectId);
    const currentPanel = container.querySelector("#subject-detail-panel");
    const markup = detailMarkup(subject, statsFor(subject, progressMap), dashboard);
    if (currentPanel) currentPanel.outerHTML = markup;
    else container.querySelector(".subjects-toolbar").insertAdjacentHTML("afterend", markup);
    bindDetailActions(container, subjects);
    container.querySelector("#subject-detail-panel")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }));
  container.querySelectorAll(".subject-building [data-edit-subject], #subjects-list [data-edit-subject]").forEach(button => button.addEventListener("click", () => openSubjectForm(subjects.find(item => item.id === button.dataset.editSubject))));
  container.querySelectorAll("[data-delete-subject]").forEach(button => button.addEventListener("click", () => deleteSubject(subjects.find(item => item.id === button.dataset.deleteSubject))));
  container.querySelectorAll("[data-plan-subject]").forEach(button => button.addEventListener("click", () => planSubjectTask(button.dataset.planSubject)));
  bindDetailActions(container, subjects);
}

function bindDetailActions(container, subjects) {
  container.querySelector("[data-close-subject]")?.addEventListener("click", () => {
    selectedSubjectId = null;
    container.querySelector("#subject-detail-panel")?.remove();
  });
  container.querySelector("#subject-detail-panel [data-edit-subject]")?.addEventListener("click", event => openSubjectForm(subjects.find(item => item.id === event.currentTarget.dataset.editSubject)));
  container.querySelector("[data-subject-tasks]")?.addEventListener("click", event => {
    const filter = qs("#task-subject-filter");
    filter.value = event.currentTarget.dataset.subjectTasks;
    location.hash = "tasks";
  });
}

function planSubjectTask(subjectId) {
  qs("#new-task-button").click();
  const subjectField = qs("#entity-form").elements.subject_id;
  if (subjectField) subjectField.value = subjectId;
}

export async function loadSubjects() {
  const data = await request("/subjects");
  setSubjects(data);
  updateSubjectFilters();
  return data;
}

export function updateSubjectFilters() {
  const select = qs("#task-subject-filter");
  const value = select.value;
  select.innerHTML = '<option value="">Todas as disciplinas</option>' + state.subjects.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("");
  select.value = value;
}

export async function renderSubjects() {
  const container = qs("#subjects-content");
  loading(container);
  try {
    const [subjects, dashboard] = await Promise.all([loadSubjects(), request("/dashboard")]);
    if (!subjects.length) {
      container.className = "subjects-shell surface";
      empty(container, { symbol: "▤", title: "Comece pelas disciplinas", message: "Cadastre as matérias do período e inaugure o primeiro prédio do campus.", action: "Inaugurar disciplina", actionId: "empty-new-subject" });
      qs("#empty-new-subject")?.addEventListener("click", () => openSubjectForm());
      return;
    }
    const progressMap = new Map(dashboard.progress_by_subject.map(item => [item.subject_id, item]));
    const focus = focusSubject(subjects, dashboard, progressMap);
    const selected = subjects.find(subject => subject.id === selectedSubjectId);
    container.className = "subjects-shell";
    container.innerHTML = `${overviewMarkup(subjects, progressMap)}${focusMarkup(focus, dashboard, statsFor(focus, progressMap))}<div class="subjects-toolbar"><div><p class="date-label">SEU DISTRITO</p><h2>Explore suas disciplinas</h2></div>${viewControlsMarkup()}</div>${detailMarkup(selected, selected ? statsFor(selected, progressMap) : null, dashboard)}${campusMarkup(subjects, progressMap)}${listMarkup(subjects)}`;
    bindSubjectActions(container, subjects, dashboard, progressMap);
  } catch {
    container.className = "subjects-shell surface";
    errorState(container, renderSubjects);
  }
}

export function openSubjectForm(subject = null) {
  const dialog = qs("#entity-dialog"), form = qs("#entity-form");
  qs("#modal-kicker").textContent = subject ? "ATUALIZAR DISCIPLINA" : "NOVA DISCIPLINA";
  qs("#modal-title").textContent = subject ? "Editar disciplina" : "Crie uma disciplina";
  qs("#modal-fields").innerHTML = fields(subject);
  form.dataset.kind = "subject";
  form.dataset.id = subject?.id || "";
  dialog.showModal();
  form.elements.name.focus();
}

export async function submitSubject(form) {
  clearErrors(form);
  setBusy(form, true);
  const raw = Object.fromEntries(new FormData(form));
  const body = { ...raw, workload_hours: Number(raw.workload_hours), professor: raw.professor || null, description: raw.description || null, period: raw.period || null, start_date: raw.start_date || null, end_date: raw.end_date || null };
  try {
    await request(form.dataset.id ? `/subjects/${form.dataset.id}` : "/subjects", { method: form.dataset.id ? "PUT" : "POST", body });
    closeEntityDialog();
    toast(form.dataset.id ? "Disciplina atualizada." : "Disciplina criada.");
    await renderSubjects();
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    showErrors(form, error.fields);
    if (!Object.keys(error.fields || {}).length) toast(error.message, "error");
  } finally {
    setBusy(form, false);
  }
}

async function deleteSubject(subject) {
  if (!await confirmAction("Excluir disciplina?", `As tarefas de “${subject.name}” também serão excluídas. Esta ação não pode ser desfeita.`)) return;
  try {
    await request(`/subjects/${subject.id}`, { method: "DELETE" });
    toast("Disciplina excluída.");
    await renderSubjects();
    window.dispatchEvent(new CustomEvent("data:changed"));
  } catch (error) {
    toast(error.message, "error");
  }
}
