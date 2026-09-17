import { request } from "./api.js?v=20260910-edu-ia1";
import { state } from "./state.js?v=20260910-edu-ia1";
import { confirmAction, empty, errorState, escapeHtml, loading, qs, toast } from "./ui.js?v=20260910-edu-ia1";

let activeConversationId = null;

function messageMarkup(message) {
  const role = message.role === "assistant" ? "assistant" : "student";
  const name = role === "assistant" ? "EDU IA" : "Você";
  return `<article class="edu-ai-message is-${role}"><span class="edu-ai-message__avatar" aria-hidden="true"><i class="ph ${role === "assistant" ? "ph-sparkle" : "ph-user"}"></i></span><div><strong>${name}</strong><p>${escapeHtml(message.content).replace(/\n/g, "<br>")}</p></div></article>`;
}

function conversationMarkup(conversation) {
  return `<button type="button" class="edu-ai-conversation${conversation.id === activeConversationId ? " is-active" : ""}" data-edu-ai-conversation="${conversation.id}"><i class="ph ph-chat-centered-text" aria-hidden="true"></i><span><strong>${escapeHtml(conversation.title)}</strong><small>${new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" }).format(new Date(conversation.updated_at))}</small></span></button>`;
}

function chatMarkup(conversation) {
  if (!conversation) {
    return `<section class="edu-ai-chat edu-ai-chat--welcome"><div class="edu-ai-orb" aria-hidden="true"><i class="ph ph-sparkle"></i></div><p class="date-label">PRONTO PARA ESTUDAR</p><h2>Como posso ajudar no seu caminho?</h2><p>Abra uma conversa ou use o botão EDU IA em uma disciplina ou tarefa para receber ajuda com o contexto certo.</p><div class="edu-ai-prompts"><button type="button" data-edu-ai-new>Dê uma dica para começar</button><button type="button" data-edu-ai-new>Explique um conceito passo a passo</button><button type="button" data-edu-ai-new>Crie um exercício semelhante</button></div></section>`;
  }
  const messages = conversation.messages.length
    ? conversation.messages.map(messageMarkup).join("")
    : `<div class="edu-ai-empty-chat"><div class="edu-ai-orb" aria-hidden="true"><i class="ph ph-sparkle"></i></div><h2>Conversa pronta</h2><p>Faça uma pergunta sobre ${escapeHtml(conversation.title)}.</p></div>`;
  return `<section class="edu-ai-chat"><header class="edu-ai-chat__header"><div><p class="date-label">CONVERSA ATIVA</p><h2>${escapeHtml(conversation.title)}</h2></div><button class="icon-button" type="button" data-edu-ai-delete="${conversation.id}" aria-label="Excluir conversa"><i class="ph ph-trash" aria-hidden="true"></i></button></header><div id="edu-ai-messages" class="edu-ai-messages">${messages}</div><form id="edu-ai-form" class="edu-ai-form"><label class="sr-only" for="edu-ai-question">Sua dúvida</label><textarea id="edu-ai-question" name="content" maxlength="4000" required aria-describedby="edu-ai-keyboard-hint" placeholder="Escreva sua dúvida para o EDU IA..."></textarea><div><small id="edu-ai-keyboard-hint">Enter envia · Shift+Enter quebra a linha</small><button class="button button--primary" type="submit"><i class="ph ph-paper-plane-tilt" aria-hidden="true"></i> Enviar mensagem</button></div></form></section>`;
}

async function loadConversation(id) {
  activeConversationId = id;
  const conversation = await request(`/edu-ia/conversations/${id}`);
  const list = await request("/edu-ia/conversations");
  renderLayout(list, conversation);
}

function renderLayout(conversations, conversation = null) {
  const content = qs("#edu-ia-content");
  content.innerHTML = `<div class="edu-ai-layout"><aside class="edu-ai-sidebar"><div class="edu-ai-sidebar__head"><span>Conversas</span><button class="icon-button" type="button" data-edu-ai-new aria-label="Nova conversa"><i class="ph ph-plus" aria-hidden="true"></i></button></div><div class="edu-ai-conversations">${conversations.length ? conversations.map(conversationMarkup).join("") : '<p class="edu-ai-sidebar__empty">Suas conversas aparecerão aqui.</p>'}</div><p class="edu-ai-notice"><i class="ph ph-shield-check" aria-hidden="true"></i> Demonstração: evite enviar dados pessoais ou respostas completas de avaliações.</p></aside>${chatMarkup(conversation)}</div>`;
  content.querySelectorAll("[data-edu-ai-conversation]").forEach(button => button.addEventListener("click", () => loadConversation(button.dataset.eduAiConversation)));
  content.querySelectorAll("[data-edu-ai-new]").forEach(button => button.addEventListener("click", () => createConversation()));
  content.querySelector("[data-edu-ai-delete]")?.addEventListener("click", async event => {
    const button = event.currentTarget;
    const conversationId = button.dataset.eduAiDelete;
    if (!await confirmAction("Excluir conversa?", "As mensagens desta conversa serão removidas permanentemente.")) return;
    button.disabled = true;
    try {
      await request(`/edu-ia/conversations/${conversationId}`, { method: "DELETE" });
      if (activeConversationId === conversationId) activeConversationId = null;
      await renderEduIA();
    } catch (error) {
      toast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });
  const form = content.querySelector("#edu-ai-form");
  form?.addEventListener("submit", sendMessage);
  form?.elements.content.addEventListener("keydown", event => {
    if (event.key !== "Enter" || event.shiftKey || event.isComposing || event.keyCode === 229) return;
    event.preventDefault();
    if (!event.repeat && form.dataset.sending !== "true") form.requestSubmit();
  });
  requestAnimationFrame(() => qs("#edu-ai-messages")?.scrollTo({ top: 999999, behavior: "smooth" }));
}

async function createConversation(context = null) {
  try {
    const conversation = await request("/edu-ia/conversations", { method: "POST", body: context || {} });
    await loadConversation(conversation.id);
    qs("#edu-ai-question")?.focus();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function sendMessage(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const content = form.elements.content.value.trim();
  if (!content || !activeConversationId || form.dataset.sending === "true") return;
  const button = form.querySelector("button[type='submit']");
  form.dataset.sending = "true";
  const buttonLabel = button.innerHTML;
  button.disabled = true;
  button.textContent = "Pensando...";
  try {
    await request(`/edu-ia/conversations/${activeConversationId}/messages`, { method: "POST", body: { content } });
    await loadConversation(activeConversationId);
  } catch (error) {
    toast(error.message, "error");
    await loadConversation(activeConversationId);
  } finally {
    form.dataset.sending = "false";
    button.disabled = false;
    button.innerHTML = buttonLabel;
    qs("#edu-ai-question")?.focus();
  }
}

export function openEduIAContext(context = {}) {
  state.eduAIContext = context;
  if (location.hash === "#edu-ia") renderEduIA();
  else location.hash = "edu-ia";
}

export async function renderEduIA() {
  const content = qs("#edu-ia-content");
  loading(content);
  try {
    const status = await request("/edu-ia");
    qs("#edu-ia-new-conversation").hidden = !status.available;
    if (!status.available) {
      content.className = "surface";
      empty(content, { symbol: "✦", title: "EDU IA em preparação", message: "O tutor precisa de uma chave Gemini configurada pelo responsável pelo projeto antes de responder dúvidas." });
      return;
    }
    content.className = "";
    if (state.eduAIContext) {
      const context = state.eduAIContext;
      state.eduAIContext = null;
      await createConversation(context);
      return;
    }
    const conversations = await request("/edu-ia/conversations");
    const current = activeConversationId ? await request(`/edu-ia/conversations/${activeConversationId}`).catch(() => null) : null;
    renderLayout(conversations, current);
  } catch {
    content.className = "surface";
    errorState(content, renderEduIA);
  }
}
