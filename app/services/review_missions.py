import json
from datetime import UTC, date, datetime

from app.integrations.edu_ia.gemini import GeminiClient, GeminiError
from app.models.review_mission import ReviewMission, ReviewMissionStatus
from app.models.subject import Subject
from app.models.task import AcademicTask


def fallback_questions(task: AcademicTask, subject: Subject) -> list[str]:
    subject_name = subject.name
    return [
        f"Em suas palavras, qual era o objetivo principal de “{task.title}”?",
        f"Qual conceito de {subject_name} foi mais importante para realizar essa tarefa?",
        "Dê um exemplo prático de como você aplicaria esse conceito em uma situação parecida.",
    ]


def ai_questions(client: GeminiClient, task: AcademicTask, subject: Subject) -> list[str]:
    instruction = (
        "Você é o EDU IA, tutor acadêmico do EduTrack. Crie EXATAMENTE 3 perguntas "
        "curtas de revisão por recuperação, em português do Brasil. Não dê respostas, "
        "não numere com explicações extras e foque no entendimento, aplicação e reflexão."
    )
    prompt = (
        f"Disciplina: {subject.name}. Tarefa concluída: {task.title}. "
        f"Contexto: {task.description or subject.description or 'sem detalhes adicionais'}"
    )
    reply = client.generate_reply(instruction, [{"role": "user", "content": prompt}])
    candidates = []
    for line in reply.splitlines():
        clean = line.strip().lstrip("-• ")
        if clean and clean[0].isdigit() and len(clean) > 4:
            clean = clean.split(".", 1)[-1].split(")", 1)[-1].strip()
        if clean.endswith("?"):
            candidates.append(clean)
    return candidates[:3] if len(candidates) >= 3 else fallback_questions(task, subject)


def create_questions(
    mission: ReviewMission,
    task: AcademicTask,
    subject: Subject,
    client: GeminiClient | None,
) -> ReviewMission:
    if not mission.questions:
        try:
            mission.questions = (
                ai_questions(client, task, subject)
                if client
                else fallback_questions(task, subject)
            )
        except GeminiError:
            mission.questions = fallback_questions(task, subject)
    mission.status = ReviewMissionStatus.IN_PROGRESS
    return mission


def fallback_assessment(answers: list[str]) -> tuple[int, str]:
    """Keep the review usable if the optional AI provider is unavailable."""
    quality = sum(min(len(answer.split()) / 18, 1) for answer in answers) / 3
    score = round(quality * 100)
    if score >= 80:
        summary = "Você já demonstra domínio da ideia central e consegue aplicar o conteúdo."
    elif score >= 55:
        summary = (
            "Você recuperou os conceitos principais. "
            "Revise um exemplo prático para consolidar."
        )
    else:
        summary = (
            "Você iniciou a recuperação do conteúdo. Releia o material e tente "
            "explicar o conceito com suas palavras."
        )
    return score, summary


def ai_assessment(
    client: GeminiClient,
    task: AcademicTask,
    subject: Subject,
    questions: list[str],
    answers: list[str],
) -> tuple[int, str]:
    instruction = (
        "Você é o EDU IA, tutor acadêmico do EduTrack. Avalie as respostas de uma "
        "missão de recuperação pelo entendimento e aplicação, não pelo tamanho. "
        "Retorne SOMENTE JSON válido, sem markdown, no formato "
        '{"mastery_percent": 0 a 100, "mastery_summary": "uma frase curta em português"}. '
        "A frase deve dizer o que o aluno já domina e, se necessário, um próximo foco."
    )
    answers_text = "\n".join(
        f"Pergunta {index + 1}: {question}\nResposta: {answers[index]}"
        for index, question in enumerate(questions)
    )
    reply = client.generate_reply(
        instruction,
        [
            {
                "role": "user",
                "content": (
                    f"Disciplina: {subject.name}. Tarefa: {task.title}.\n{answers_text}"
                ),
            }
        ],
    )
    payload = json.loads(reply.removeprefix("```json").removesuffix("```").strip())
    score = int(payload["mastery_percent"])
    summary = str(payload["mastery_summary"]).strip()
    if not 0 <= score <= 100 or not summary:
        raise ValueError("Avaliação de domínio inválida.")
    return score, summary


def assess_answers(
    mission: ReviewMission,
    task: AcademicTask,
    subject: Subject,
    answers: list[str],
    client: GeminiClient | None,
) -> ReviewMission:
    meaningful = [answer.strip() for answer in answers]
    try:
        score, summary = (
            ai_assessment(client, task, subject, mission.questions, meaningful)
            if client
            else fallback_assessment(meaningful)
        )
    except (GeminiError, ValueError, json.JSONDecodeError, KeyError, TypeError):
        score, summary = fallback_assessment(meaningful)
    mission.answers = meaningful
    mission.mastery_percent = score
    mission.mastery_summary = summary
    mission.status = ReviewMissionStatus.COMPLETED
    mission.completed_at = datetime.now(UTC)
    return mission


def is_available(mission: ReviewMission, today: date) -> bool:
    return mission.due_date <= today and mission.status != ReviewMissionStatus.COMPLETED
