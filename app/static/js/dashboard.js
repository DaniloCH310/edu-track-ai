import { request } from "./api.js";
import { qs, empty, escapeHtml, formatDate, loading, errorState, toast } from "./ui.js";

const metricIcons = ["ph-chart-bar", "ph-book-open", "ph-calendar-dots", "ph-clock"];
const campusZones = ["lab", "library", "studio", "engineering"];

function statusFor(subject) {
  if (!subject.total_tasks) return "locked";
  if (subject.progress >= 100) return "completed";
  if (subject.progress > 0) return "current";
  return "next";
}

function campusLevel(progress) {
  const level = Math.max(1, Math.min(4, Math.ceil(progress / 25)));
  const stars = Math.max(1, Math.min(3, Math.ceil(progress / 34)));
  return `<span>Nível ${level}</span><span class="campus-stars" aria-label="${stars} de 3 estrelas">${[1, 2, 3].map(index => `<i class="${index <= stars ? "ph-fill" : "ph"} ph-star${index <= stars ? " star--earned" : ""}" aria-hidden="true"></i>`).join("")}</span>`;
}

function nextDueDate(subjectName, upcoming) {
  const task = upcoming.find(item => item.subject_name === subjectName);
  return task ? formatDate(task.due_date, { day: "2-digit", month: "short" }) : "Sem prazo pendente";
}

function campusMilestones(progress) {
  const milestones = [25, 50, 75, 100];
  const unlocked = milestones.filter(mark => progress >= mark).length;
  return `<span class="campus-milestones" aria-label="${unlocked} de 4 marcos desbloqueados">${milestones.map(mark => `<i class="campus-milestone${progress >= mark ? " is-reached" : ""}" aria-hidden="true" title="${mark}%"></i>`).join("")}</span>`;
}

function preferredCampusZone(subjectName) {
  const normalized = subjectName.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  if (/(banco|dados|database|sql)/.test(normalized)) return "library";
  if (/(ux|ui|design|interface)/.test(normalized)) return "studio";
  if (/(algorit|logica|matemat|calculo)/.test(normalized)) return "engineering";
  return "lab";
}

function campusMarkup(subjects, upcoming) {
  const ordered = [...subjects].sort((left, right) => right.progress - left.progress).slice(0, campusZones.length);
  const usedZones = new Set();
  return ordered.map(subject => {
    const state = statusFor(subject);
    const preferredZone = preferredCampusZone(subject.subject_name);
    const zone = !usedZones.has(preferredZone) ? preferredZone : campusZones.find(item => !usedZones.has(item));
    usedZones.add(zone);
    const taskCopy = subject.total_tasks === 1 ? "tarefa" : "tarefas";
    const stateCopy = state === "completed" ? "Área concluída" : state === "current" ? "Em construção" : state === "locked" ? "Aguardando tarefas" : "Próxima área";
    return `<button class="campus-building campus-building--${zone} is-${state}" type="button" aria-label="Explorar ${escapeHtml(subject.subject_name)}" aria-expanded="false">
      <span class="campus-building-label"><span><strong>${escapeHtml(subject.subject_name)}</strong><b>${subject.progress}%</b></span><i><span style="width:${subject.progress}%"></span></i><small>${stateCopy}</small></span>
      ${campusMilestones(subject.progress)}
      <span class="campus-tooltip" role="tooltip">
        <strong>${escapeHtml(subject.subject_name)}</strong>
        <span class="tooltip-progress"><span style="width:${subject.progress}%"></span></span>
        <span><b>${subject.progress}%</b> concluído</span>
        <span>${subject.completed_tasks} de ${subject.total_tasks} ${taskCopy}</span>
        <span>Próximo prazo: <b>${escapeHtml(nextDueDate(subject.subject_name, upcoming))}</b></span>
      </span>
    </button>`;
  }).join("");
}

function bindCampusBuildings(container) {
  container.querySelectorAll(".campus-building").forEach(building => {
    building.addEventListener("click", event => {
      const open = event.currentTarget.getAttribute("aria-expanded") !== "true";
      container.querySelectorAll(".campus-building").forEach(item => item.setAttribute("aria-expanded", "false"));
      event.currentTarget.setAttribute("aria-expanded", String(open));
    });
  });
}

function renderLegend() {
  qs("#campus-legend").innerHTML = `
    <span><i class="legend-dot is-completed"></i>Concluído</span>
    <span><i class="legend-dot is-current"></i>Em andamento</span>
    <span><i class="legend-dot is-next"></i>Próxima etapa</span>
    <span><i class="legend-dot is-locked"></i>Bloqueado</span>`;
}

function renderNextBestAction(recommendation) {
  let panel = qs("#study-plan");
  if (!panel) {
    panel = document.createElement("section");
    panel.id = "study-plan";
  }
  panel.className = "study-plan study-plan--next-action surface campus-next-action";
  qs(".campus-panel").after(panel);
  if (!recommendation) {
    panel.innerHTML = '<div class="study-plan__icon" aria-hidden="true"><i class="ph ph-check-circle"></i></div><div><p class="date-label">PRÓXIMA MELHOR AÇÃO</p><h2>Seu plano está em dia</h2><p>Crie uma tarefa para receber uma recomendação de estudo personalizada.</p></div><a class="button button--ghost" href="#tasks">Ver tarefas</a>';
    return;
  }
  const priority = recommendation.priority === "urgent" ? "Urgente" : recommendation.priority === "attention" ? "Atenção" : "Próximo passo";
  const action = recommendation.status === "pending"
    ? `<button class="button button--primary" type="button" data-start-recommended-task="${recommendation.id}">Começar agora</button>`
    : '<a class="button button--primary" href="#agenda">Continuar tarefa</a>';
  panel.innerHTML = `<div class="study-plan__icon is-${recommendation.priority}" aria-hidden="true"><i class="ph ph-sparkle"></i></div><div class="study-plan__copy"><p class="date-label">PRÓXIMA MELHOR AÇÃO</p><h2>${escapeHtml(recommendation.title)}</h2><p><strong>${escapeHtml(recommendation.subject_name)}</strong> · prazo ${formatDate(recommendation.due_date, { day: "2-digit", month: "long" })}</p><small>${escapeHtml(recommendation.reason)}</small></div><div class="study-plan__action"><span class="study-plan__priority is-${recommendation.priority}">${priority}</span>${action}</div>`;
  panel.querySelector("[data-start-recommended-task]")?.addEventListener("click", async event => {
    const button = event.currentTarget;
    button.disabled = true;
    button.textContent = "Iniciando...";
    try {
      await request(`/tasks/${recommendation.id}/status`, { method: "PATCH", body: { status: "in_progress" } });
      toast("Tarefa iniciada. Bom estudo!");
      window.dispatchEvent(new CustomEvent("data:changed"));
    } catch (error) {
      button.disabled = false;
      button.textContent = "Começar agora";
      toast(error.message, "error");
    }
  });
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

function renderOnboarding(data) {
  let panel = qs("#onboarding-card");
  if (data.total_subjects && data.total_tasks) {
    panel?.remove();
    return;
  }
  if (!panel) {
    panel = document.createElement("section");
    panel.id = "onboarding-card";
    panel.className = "onboarding-card surface";
    (qs("#study-plan") || qs(".dashboard-grid")).before(panel);
  }
  const needsSubject = !data.total_subjects;
  panel.innerHTML = `<div class="onboarding-card__copy"><p class="date-label">PRIMEIROS PASSOS</p><h2>${needsSubject ? "Comece em 2 passos" : "Falta só mais um passo"}</h2><p>${needsSubject ? "Monte sua base para que o EduTrack organize seus próximos estudos." : "Sua disciplina já está pronta. Agora registre uma entrega para montar seu plano."}</p></div><ol class="onboarding-steps"><li class="${needsSubject ? "is-active" : "is-complete"}"><span>1</span><div><strong>Crie uma disciplina</strong><small>${needsSubject ? "Matéria, professor e período" : "Concluído"}</small></div></li><li class="${needsSubject ? "is-locked" : "is-active"}"><span>2</span><div><strong>Adicione uma tarefa</strong><small>${needsSubject ? "Disponível após a disciplina" : "Defina o próximo prazo"}</small></div></li></ol><button class="button button--primary" type="button" id="onboarding-action">${needsSubject ? "Criar primeira disciplina" : "Criar primeira tarefa"}</button>`;
  qs("#onboarding-action")?.addEventListener("click", () => { location.hash = needsSubject ? "subjects" : "tasks"; });
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
    renderOnboarding(data);
    renderNextBestAction(data.recommended_task);
    const cards = [
      ["Progresso geral", `${data.overall_progress}%`, `${data.completed_tasks} de ${data.total_tasks} tarefas`, "var(--primary-soft)"],
      ["Disciplinas", data.total_subjects, "frentes de estudo", "var(--success-soft)"],
      ["Próximos 3 dias", data.due_soon, "entregas no radar", "var(--warning-soft)"],
      ["Em atraso", data.overdue, data.overdue ? "pedem sua atenção" : "tudo em dia", "var(--danger-soft)"],
    ];
    metrics.innerHTML = cards.map(([label, value, note, color], index) => `<article class="metric" style="--metric-color:${color}"><i class="ph ${metricIcons[index]} metric-icon" aria-hidden="true"></i><div><span>${label}</span><strong>${value}</strong><small>${note}</small></div></article>`).join("");
    qs("#campus-level").innerHTML = campusLevel(data.overall_progress);
    qs("#campus-progress-value").textContent = `${data.overall_progress}%`;
    qs("#campus-progress-bar").style.width = `${data.overall_progress}%`;
    if (!data.progress_by_subject.length) {
      empty(progress, { title: "Seu campus começa aqui", message: "Crie uma disciplina para inaugurar o primeiro prédio.", action: "Criar disciplina", actionId: "campus-new-subject" });
      qs("#campus-new-subject")?.addEventListener("click", () => { location.hash = "subjects"; });
    } else {
      progress.innerHTML = campusMarkup(data.progress_by_subject, data.upcoming);
      bindCampusBuildings(progress);
    }
    if (!data.upcoming.length) {
      qs(".campus-missions").classList.add("is-empty");
      upcoming.innerHTML = '<div class="agenda-empty"><img src="/static/assets/agenda-clear.png" alt="Calendário com tarefa concluída"><h2>Agenda tranquila</h2><p>Não há entregas pendentes no momento.</p></div>';
    } else {
      qs(".campus-missions").classList.remove("is-empty");
      upcoming.innerHTML = `<div class="upcoming-list">${data.upcoming.map(item => `<article class="upcoming-item"><span class="upcoming-dot" style="--dot-color:var(--primary)"></span><p>${escapeHtml(item.title)}<small>${escapeHtml(item.subject_name)}</small></p><span class="upcoming-date">${formatDate(item.due_date)}</span></article>`).join("")}</div>`;
    }
  } catch {
    errorState(progress, renderDashboard);
    errorState(upcoming, renderDashboard);
    metrics.innerHTML = "";
  }
}
