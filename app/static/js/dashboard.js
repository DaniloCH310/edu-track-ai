import { request } from "./api.js?v=20260906-campus2";
import { qs, empty, escapeHtml, formatDate, loading, errorState, toast } from "./ui.js?v=20260906-campus2";

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

function campusIdentity(subjectName) {
  const normalized = subjectName.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  if (/(banco|dados|database|sql)/.test(normalized)) {
    return {
      key: "archive",
      icon: "ph-archive-box",
      label: "Arquivo de registros",
      milestones: ["Primeiro registro", "Índices organizados", "Relações conectadas", "Acervo consolidado"],
    };
  }
  if (/(python|program|codigo|code)/.test(normalized)) {
    return {
      key: "lab",
      icon: "ph-flask",
      label: "Laboratório de código",
      milestones: ["Ambiente preparado", "Funções testadas", "Projeto em execução", "Laboratório mestre"],
    };
  }
  if (/(ux|ui|design|interface)/.test(normalized)) {
    return {
      key: "studio",
      icon: "ph-paint-brush",
      label: "Estúdio de interfaces",
      milestones: ["Referências reunidas", "Fluxo desenhado", "Protótipo validado", "Experiência concluída"],
    };
  }
  if (/(algorit|logica|matemat|calculo)/.test(normalized)) {
    return {
      key: "engineering",
      icon: "ph-cpu",
      label: "Oficina de algoritmos",
      milestones: ["Base lógica", "Estruturas montadas", "Soluções refinadas", "Oficina concluída"],
    };
  }
  return {
    key: "campus",
    icon: "ph-books",
    label: "Centro de estudos",
    milestones: ["Base inaugurada", "Rota definida", "Conhecimento aplicado", "Área concluída"],
  };
}

function campusMilestones(progress, labels) {
  const milestones = [25, 50, 75, 100];
  const unlocked = milestones.filter(mark => progress >= mark).length;
  const reached = labels.slice(0, unlocked);
  const next = labels[unlocked] || "Todos os marcos desbloqueados";
  return `<span class="campus-milestones" aria-label="${unlocked} de 4 marcos desbloqueados: ${escapeHtml(reached.join(", ") || "nenhum")}. Próximo marco: ${escapeHtml(next)}">${milestones.map((mark, index) => `<i class="campus-milestone${progress >= mark ? " is-reached" : ""}" aria-hidden="true" title="${escapeHtml(labels[index])}: ${mark}%"></i>`).join("")}</span>`;
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
    const identity = campusIdentity(subject.subject_name);
    const unlocked = identity.milestones.filter((_, index) => subject.progress >= [25, 50, 75, 100][index]).length;
    const currentMilestone = identity.milestones[Math.min(unlocked, identity.milestones.length - 1)];
    const taskCopy = subject.total_tasks === 1 ? "tarefa" : "tarefas";
    const stateCopy = state === "completed" ? "Área concluída" : state === "current" ? "Em construção" : state === "locked" ? "Aguardando tarefas" : "Próxima área";
    return `<button class="campus-building campus-building--${zone} campus-identity--${identity.key} is-${state}" type="button" aria-label="Explorar ${escapeHtml(subject.subject_name)}: ${identity.label}, ${subject.progress}% concluído e ${unlocked} de 4 marcos desbloqueados" aria-expanded="false">
      <i class="campus-landmark ph ${identity.icon}" aria-hidden="true"></i>
      <span class="campus-building-label"><span><strong>${escapeHtml(subject.subject_name)}</strong><b>${subject.progress}%</b></span><i><span style="width:${subject.progress}%"></span></i><span class="campus-building-identity"><i class="ph ${identity.icon}" aria-hidden="true"></i>${escapeHtml(identity.label)}</span><small>${stateCopy} · ${unlocked}/4 marcos</small></span>
      ${campusMilestones(subject.progress, identity.milestones)}
      <span class="campus-tooltip" role="tooltip">
        <strong>${escapeHtml(subject.subject_name)}</strong>
        <span class="tooltip-identity"><i class="ph ${identity.icon}" aria-hidden="true"></i>${escapeHtml(identity.label)}</span>
        <span class="tooltip-progress"><span style="width:${subject.progress}%"></span></span>
        <span><b>${subject.progress}%</b> concluído</span>
        <span>${subject.completed_tasks} de ${subject.total_tasks} ${taskCopy}</span>
        <span>Marco atual: <b>${escapeHtml(currentMilestone)}</b></span>
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

function availableMinutes() {
  const saved = Number(localStorage.getItem("edutrack-available-minutes"));
  return [15, 25, 45, 60, 90].includes(saved) ? saved : 25;
}

function availabilityControl(minutes) {
  return `<label class="study-plan__availability">Tenho <select data-available-minutes aria-label="Tempo disponível agora">${[15, 25, 45, 60, 90].map(value => `<option value="${value}" ${value === minutes ? "selected" : ""}>${value} min</option>`).join("")}</select> agora</label>`;
}

function renderNextBestAction(recommendation, minutes) {
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
  const action = recommendation.action_type === "edu_ai"
    ? `<button class="button button--primary" type="button" data-edu-ai-task="${recommendation.id}">Revisar com EDU IA</button>`
    : `<button class="button button--primary" type="button" data-open-recommended-task="${recommendation.id}">Abrir missão</button>`;
  panel.innerHTML = `<div class="study-plan__icon is-${recommendation.priority}" aria-hidden="true"><i class="ph ph-sparkle"></i></div><div class="study-plan__copy"><p class="date-label">MINHA PRÓXIMA AÇÃO</p><h2>${escapeHtml(recommendation.title)}</h2><p><strong>${escapeHtml(recommendation.subject_name)}</strong> · ${recommendation.estimated_minutes} min · dificuldade ${recommendation.difficulty}/5</p><small>${escapeHtml(recommendation.reason)}</small></div><div class="study-plan__action"><span class="study-plan__priority is-${recommendation.priority}">${priority}</span>${action}${availabilityControl(minutes)}</div>`;
  panel.querySelector("[data-available-minutes]")?.addEventListener("change", event => {
    localStorage.setItem("edutrack-available-minutes", event.currentTarget.value);
    renderDashboard();
  });
  panel.querySelector("[data-open-recommended-task]")?.addEventListener("click", event => {
    sessionStorage.setItem("edutrack-focus-task", event.currentTarget.dataset.openRecommendedTask);
    location.hash = "tasks";
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

function reviewAvailabilityCopy(mission) {
  if (mission.status === "completed") return `Domínio ${mission.mastery_percent ?? 0}%`;
  if (mission.is_available) return "Disponível para revisar";
  const today = new Date();
  const due = new Date(`${mission.due_date}T12:00:00`);
  const days = Math.max(1, Math.ceil((due - new Date(today.getFullYear(), today.getMonth(), today.getDate())) / 86400000));
  return `Revisão em ${days} ${days === 1 ? "dia" : "dias"}`;
}

function reviewMissionMarkup(mission) {
  const completed = mission.status === "completed";
  const action = completed
    ? `<span class="review-mission__mastery"><i class="ph-fill ph-brain" aria-hidden="true"></i>${mission.mastery_percent ?? 0}% domínio</span>`
    : mission.is_available
      ? `<button class="review-mission__action" type="button" data-start-review="${mission.id}">Revisar com EDU IA <i class="ph ph-arrow-right" aria-hidden="true"></i></button>`
      : `<span class="review-mission__schedule"><i class="ph ph-clock" aria-hidden="true"></i>${reviewAvailabilityCopy(mission)}</span>`;
  return `<article class="review-mission${completed ? " is-completed" : ""}">
    <div class="review-mission__icon"><i class="ph ${completed ? "ph-check-circle" : "ph-arrows-clockwise"}" aria-hidden="true"></i></div>
    <div class="review-mission__copy"><span>MISSÃO DE REVISÃO</span><strong>${escapeHtml(mission.task_title)}</strong><small>${escapeHtml(mission.subject_name)} · ${completed ? escapeHtml(mission.mastery_summary || "Revisão concluída.") : formatDate(mission.due_date, { day: "2-digit", month: "short" })}</small></div>
    ${action}
  </article>`;
}

function closeReviewDialog() {
  document.querySelector(".review-dialog-backdrop")?.remove();
}

function openReviewDialog(mission) {
  closeReviewDialog();
  const dialog = document.createElement("div");
  dialog.className = "review-dialog-backdrop";
  dialog.innerHTML = `<section class="review-dialog" role="dialog" aria-modal="true" aria-labelledby="review-dialog-title">
    <button class="review-dialog__close" type="button" aria-label="Fechar revisão"><i class="ph ph-x" aria-hidden="true"></i></button>
    <div class="review-dialog__eyebrow"><i class="ph-fill ph-sparkle" aria-hidden="true"></i> EDU IA · recuperação ativa</div>
    <h2 id="review-dialog-title">Vamos relembrar <em>${escapeHtml(mission.task_title)}</em>?</h2>
    <p>Responda sem consultar o material primeiro. Depois, o EDU IA mostra o que você já domina.</p>
    <form class="review-dialog__form">
      ${mission.questions.map((question, index) => `<label><span>${index + 1}</span><strong>${escapeHtml(question)}</strong><textarea name="answer-${index}" rows="2" required placeholder="Escreva com suas palavras..."></textarea></label>`).join("")}
      <button class="button button--primary" type="submit">Ver meu domínio <i class="ph ph-arrow-right" aria-hidden="true"></i></button>
    </form>
  </section>`;
  document.body.append(dialog);
  dialog.querySelector(".review-dialog__close").addEventListener("click", closeReviewDialog);
  dialog.addEventListener("click", event => { if (event.target === dialog) closeReviewDialog(); });
  dialog.querySelector("textarea")?.focus();
  dialog.querySelector("form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const answers = [...form.querySelectorAll("textarea")].map(field => field.value.trim());
    if (answers.some(answer => !answer)) {
      toast("Responda às três perguntas para concluir a missão.", "error");
      return;
    }
    const button = form.querySelector("button");
    button.disabled = true;
    button.textContent = "Analisando...";
    try {
      const completed = await request(`/reviews/${mission.id}/submit`, { method: "POST", body: { answers } });
      dialog.querySelector(".review-dialog").innerHTML = `<button class="review-dialog__close" type="button" aria-label="Fechar revisão"><i class="ph ph-x" aria-hidden="true"></i></button><div class="review-result"><i class="ph-fill ph-brain" aria-hidden="true"></i><span>MAPA DE DOMÍNIO ATUALIZADO</span><strong>${completed.mastery_percent}%</strong><h2>${escapeHtml(completed.mastery_summary || "Missão concluída.")}</h2><p>A recuperação após alguns dias ajuda a consolidar o que você estudou. Continue construindo seu campus.</p><button class="button button--primary" type="button">Concluir</button></div>`;
      dialog.querySelector(".review-dialog__close").addEventListener("click", () => { closeReviewDialog(); window.dispatchEvent(new CustomEvent("data:changed")); });
      dialog.querySelector(".review-result .button").addEventListener("click", () => { closeReviewDialog(); window.dispatchEvent(new CustomEvent("data:changed")); });
    } catch (error) {
      button.disabled = false;
      button.textContent = "Ver meu domínio";
      toast(error.message, "error");
    }
  });
}

async function startReviewMission(mission) {
  try {
    const started = await request(`/reviews/${mission.id}/start`, { method: "POST" });
    openReviewDialog(started);
  } catch (error) {
    toast(error.message, "error");
  }
}

function renderMissionRadar(data, container) {
  const reviews = data.review_missions || [];
  const hasMissions = reviews.length || data.upcoming.length;
  qs(".campus-missions").classList.toggle("is-empty", !hasMissions);
  if (!hasMissions) {
    container.innerHTML = '<div class="agenda-empty"><img src="/static/assets/agenda-clear.png" alt="Calendário com tarefa concluída"><h2>Agenda tranquila</h2><p>Conclua uma tarefa e uma revisão aparecerá aqui alguns dias depois.</p></div>';
    return;
  }
  const deliveries = data.upcoming.length ? `<div class="mission-divider">Entregas no radar</div><div class="upcoming-list">${data.upcoming.map(item => `<article class="upcoming-item"><span class="upcoming-dot" style="--dot-color:var(--primary)"></span><p>${escapeHtml(item.title)}<small>${escapeHtml(item.subject_name)}</small></p><span class="upcoming-date">${formatDate(item.due_date)}</span></article>`).join("")}</div>` : "";
  container.innerHTML = `${reviews.length ? `<div class="review-mission-list">${reviews.map(reviewMissionMarkup).join("")}</div>` : ""}${deliveries}`;
  container.querySelectorAll("[data-start-review]").forEach(button => {
    button.addEventListener("click", () => startReviewMission(reviews.find(mission => String(mission.id) === button.dataset.startReview)));
  });
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
    const minutes = availableMinutes();
    const data = await request(`/dashboard?available_minutes=${minutes}`);
    renderOnboarding(data);
    renderNextBestAction(data.recommended_task, minutes);
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
    renderMissionRadar(data, upcoming);
  } catch {
    errorState(progress, renderDashboard);
    errorState(upcoming, renderDashboard);
    metrics.innerHTML = "";
  }
}
