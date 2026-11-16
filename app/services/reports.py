"""Read-only weekly report rendering; no stored files or third-party requests."""

from datetime import UTC, date, datetime, timedelta
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.services.dashboard import percentage

STATUS_LABELS = {
    TaskStatus.PENDING: "Pendente",
    TaskStatus.IN_PROGRESS: "Em andamento",
    TaskStatus.COMPLETED: "Concluída",
}


def render_weekly_pdf(
    name: str,
    subjects: list[Subject],
    tasks: list[AcademicTask],
    first: date,
    zone: ZoneInfo,
) -> bytes:
    last = first + timedelta(days=6)
    next_end = last + timedelta(days=7)
    planned = [task for task in tasks if first <= task.due_date <= last]
    completed = []
    for task in tasks:
        if task.status != TaskStatus.COMPLETED or task.completed_at is None:
            continue
        stamp = task.completed_at
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=UTC)
        if first <= stamp.astimezone(zone).date() <= last:
            completed.append(task)
    backlog = [
        task for task in tasks if task.due_date < first and task.status != TaskStatus.COMPLETED
    ]
    upcoming = [
        task
        for task in tasks
        if last < task.due_date <= next_end and task.status != TaskStatus.COMPLETED
    ]
    done = sum(task.status == TaskStatus.COMPLETED for task in planned)
    pending = len(planned) - done
    subject_names = {subject.id: subject.name for subject in subjects}
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportCell",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#272134"),
            splitLongWords=True,
        )
    )
    styles["Title"].textColor = colors.HexColor("#6750A4")
    styles["Heading2"].textColor = colors.HexColor("#6750A4")
    styles["Heading2"].spaceBefore = 18
    styles["Heading2"].keepWithNext = True
    styles.add(ParagraphStyle(
        "ReportIntro", parent=styles["ReportCell"], keepWithNext=True, spaceAfter=3 * mm,
    ))
    story = []

    def paragraph(value, style="ReportCell"):
        # Treat every user value as text, never ReportLab XML or an external resource.
        return Paragraph(escape(str(value)), styles[style])

    def table(headers, rows, widths):
        cells = [[paragraph(value) for value in headers]]
        cells.extend([[paragraph(value) for value in row] for row in rows])
        result = LongTable(cells, colWidths=[width * mm for width in widths], repeatRows=1)
        result.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#FAF8FD")],
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#C8B8E6")),
                ]
            )
        )
        story.append(result)

    def task_section(title, items, empty):
        story.append(paragraph(title, "Heading2"))
        if not items:
            story.append(paragraph(empty))
            return
        table(
            ["Tarefa / disciplina", "Prazo", "Status atual"],
            [
                [
                    f"{task.title}\n({subject_names[task.subject_id]})",
                    task.due_date.strftime("%d/%m/%Y"),
                    STATUS_LABELS[task.status],
                ]
                for task in sorted(items, key=lambda task: (task.due_date, task.title.casefold()))
            ],
            [100, 32, 38],
        )

    story.extend(
        [
            paragraph("EduTrack AI | Relatório semanal", "Title"),
            paragraph(f"{first:%d/%m/%Y} a {last:%d/%m/%Y}", "Heading2"),
            paragraph(f"Estudante: {name}"),
            paragraph(f"Gerado em {datetime.now(zone):%d/%m/%Y %H:%M} ({zone.key})"),
            Spacer(1, 5 * mm),
            paragraph(
                f"{done} de {len(planned)} tarefas com prazo nesta semana estão concluídas. "
                f"Progresso dessas entregas: {percentage(done, len(planned))}%."
            ),
            paragraph(
                f"{len(completed)} conclusões registradas no período, independentemente do prazo. "
                f"{pending} tarefas da semana seguem em aberto."
            ),
            Spacer(1, 3 * mm),
            paragraph(
                "Retrato dos dados atuais. Os status e o progresso não reconstituem o estado "
                "de semanas passadas. Conclusões sem data registrada não entram na contagem "
                "do período. Nenhum prazo foi alterado."
            ),
        ]
    )
    task_section("Entregas com prazo na semana", planned, "Nenhuma tarefa com prazo neste período.")
    task_section(
        "O que avançou no período",
        completed,
        "Nenhuma conclusão registrada no período. Isso não mede todo o seu esforço.",
    )
    task_section("Pendências anteriores", backlog, "Nenhuma pendência anterior à semana.")
    task_section("Próxima semana", upcoming, "Nenhuma entrega aberta prevista na próxima semana.")
    story.append(
        paragraph(
            "Para se reorganizar, escolha uma pendência e reserve um primeiro bloco "
            "de até 25 minutos. "
            "Ajuste ao tempo disponível e combine novos prazos quando necessário."
            if pending or backlog or upcoming
            else "Você pode reservar um bloco leve de revisão ou deixar espaço para descansar."
        )
    )
    story.append(paragraph("Progresso atual por disciplina", "Heading2"))
    story.append(paragraph(
        "Considera todas as tarefas cadastradas, independentemente da semana.", "ReportIntro",
    ))
    rows = []
    for subject in sorted(subjects, key=lambda subject: subject.name.casefold()):
        related = [task for task in tasks if task.subject_id == subject.id]
        count = sum(task.status == TaskStatus.COMPLETED for task in related)
        rows.append(
            [subject.name, f"{count} de {len(related)}", f"{percentage(count, len(related))}%"]
        )
    if rows:
        table(["Disciplina", "Concluídas / total", "Progresso"], rows, [100, 40, 30])
    else:
        story.append(paragraph("Nenhuma disciplina cadastrada."))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#655C70"))
        canvas.drawString(20 * mm, 13 * mm, "EduTrack AI - acompanhamento acadêmico")
        canvas.drawRightString(190 * mm, 13 * mm, f"Página {doc.page}")
        canvas.restoreState()

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=23 * mm,
        title="EduTrack AI - Relatório semanal",
        author="EduTrack AI",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
