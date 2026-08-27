from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pandas as pd
import streamlit as st

st.set_page_config(page_title="EduTrack AI", page_icon="🎓", layout="wide")


def seed_data():
    today = date.today()
    subjects = [
        {"id": "python", "name": "Python Aplicado", "professor": "Marina Costa", "hours": 80, "description": "Lógica, dados e automação.", "period": "2026.2", "color": "#6750A4"},
        {"id": "ux", "name": "UX e Interfaces", "professor": "Rafael Lima", "hours": 60, "description": "Experiência do usuário e prototipação.", "period": "2026.2", "color": "#00796B"},
        {"id": "database", "name": "Banco de Dados", "professor": "Ana Souza", "hours": 60, "description": "Modelagem e consultas SQL.", "period": "2026.2", "color": "#E67E22"},
    ]
    tasks = [
        {"id": "t1", "subject_id": "python", "title": "Finalizar exercício de funções", "description": "Resolver a lista 3.", "due": today + timedelta(days=1), "status": "Em andamento"},
        {"id": "t2", "subject_id": "python", "title": "Revisar listas e dicionários", "description": "Preparação para o laboratório.", "due": today + timedelta(days=5), "status": "Concluída"},
        {"id": "t3", "subject_id": "ux", "title": "Wireframe do dashboard", "description": "Criar a versão de baixa fidelidade.", "due": today + timedelta(days=3), "status": "Pendente"},
        {"id": "t4", "subject_id": "database", "title": "Modelar entidades do projeto", "description": "Entregar diagrama ER.", "due": today - timedelta(days=1), "status": "Pendente"},
        {"id": "t5", "subject_id": "database", "title": "Praticar consultas SELECT", "description": "Exercícios de filtros e joins.", "due": today + timedelta(days=7), "status": "Concluída"},
    ]
    return subjects, tasks


def initialise():
    if "subjects" not in st.session_state:
        st.session_state.subjects, st.session_state.tasks = seed_data()
    st.session_state.setdefault("theme", "Claro")


def subject_name(subject_id):
    return next((item["name"] for item in st.session_state.subjects if item["id"] == subject_id), "Sem disciplina")


def progress(subject_id):
    items = [task for task in st.session_state.tasks if task["subject_id"] == subject_id]
    return round(100 * sum(task["status"] == "Concluída" for task in items) / len(items)) if items else 0


def inject_style():
    dark = st.session_state.theme == "Escuro"
    background, surface, text = ("#11131a", "#1b1e27", "#f4f2ff") if dark else ("#f6f7fb", "#ffffff", "#1c1b20")
    muted = "#c8c4d0" if dark else "#5f5b66"
    st.markdown(f"""<style>
      .stApp {{ background:{background}; color:{text}; }} .block-container {{ padding-top:2.2rem; max-width:1200px; }}
      h1,h2,h3,p,label {{ color:{text} !important; }} [data-testid="stSidebar"] {{ background:{surface}; }}
      .metric-card {{ background:{surface}; border:1px solid {'#373945' if dark else '#e7e4ed'}; border-radius:18px; padding:1.1rem 1.25rem; min-height:125px; }}
      .metric-card p {{ margin:0; color:{muted} !important; font-size:.9rem; }} .metric-card strong {{ font-size:2rem; display:block; margin:.35rem 0; }}
      .subject-card {{ background:{surface}; border-radius:16px; padding:1rem 1.1rem; border-left:5px solid var(--accent); margin-bottom:.7rem; }}
      .subject-card p {{ margin:.2rem 0; color:{muted} !important; }} .eyebrow {{ color:#8068cb !important; font-weight:700; letter-spacing:.07em; text-transform:uppercase; font-size:.78rem; }}
      .insight {{ background:{'#292439' if dark else '#f0ebff'}; padding:1rem; border-radius:14px; margin-bottom:.6rem; }}
    </style>""", unsafe_allow_html=True)


def page_dashboard():
    tasks = st.session_state.tasks
    total, completed = len(tasks), sum(task["status"] == "Concluída" for task in tasks)
    overdue = sum(task["due"] < date.today() and task["status"] != "Concluída" for task in tasks)
    due_soon = sum(0 <= (task["due"] - date.today()).days <= 3 and task["status"] != "Concluída" for task in tasks)
    overall = round(100 * completed / total) if total else 0
    st.markdown("<p class='eyebrow'>Seu espaço de aprendizagem</p>", unsafe_allow_html=True)
    st.title("Olá, estudante 👋")
    st.caption("Acompanhe seu ritmo e transforme suas próximas ações em progresso.")
    labels = ["Progresso geral", "Tarefas concluídas", "Próximos 3 dias", "Em atraso"]
    values = [f"{overall}%", completed, due_soon, overdue]
    details = ["do semestre", f"de {total} tarefas", "para priorizar", "pedem atenção"]
    for column, label, value, detail in zip(st.columns(4), labels, values, details):
        column.markdown(f"<div class='metric-card'><p>{label}</p><strong>{value}</strong><p>{detail}</p></div>", unsafe_allow_html=True)
    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Progresso por disciplina")
        chart = pd.DataFrame({"Disciplina":[s["name"] for s in st.session_state.subjects], "Progresso (%)":[progress(s["id"]) for s in st.session_state.subjects]}).set_index("Disciplina")
        st.bar_chart(chart, color="#6750A4")
    with right:
        st.subheader("Próximas entregas")
        upcoming = sorted([task for task in tasks if task["status"] != "Concluída"], key=lambda item:item["due"])[:4]
        if not upcoming: st.success("Tudo concluído. Ótimo trabalho!")
        for task in upcoming:
            days = (task["due"] - date.today()).days
            label = "Atrasada" if days < 0 else "Hoje" if days == 0 else f"em {days} dia(s)"
            st.markdown(f"**{task['title']}**  \n{subject_name(task['subject_id'])} · {label}")
            st.divider()
    st.subheader("Suas disciplinas")
    subjects = st.session_state.subjects
    for index, subject in enumerate(subjects):
        with st.columns(min(3, len(subjects)))[index % min(3, len(subjects))]:
            value = progress(subject["id"])
            st.markdown(f"<div class='subject-card' style='--accent:{subject['color']}'><b>{subject['name']}</b><p>{subject['professor']} · {subject['hours']}h</p><p>{value}% concluído</p></div>", unsafe_allow_html=True)
            st.progress(value / 100)


def page_subjects():
    st.title("Disciplinas")
    with st.expander("+ Adicionar disciplina"):
        with st.form("new_subject", clear_on_submit=True):
            name, professor = st.text_input("Nome da disciplina"), st.text_input("Professor(a)")
            one, two = st.columns(2); hours, period = one.number_input("Carga horária", 1, 500, 60), two.text_input("Período", "2026.2")
            description = st.text_area("Descrição")
            if st.form_submit_button("Salvar disciplina", type="primary") and name.strip():
                st.session_state.subjects.append({"id":str(uuid4()), "name":name.strip(), "professor":professor.strip() or "Não informado", "hours":hours, "description":description.strip(), "period":period.strip(), "color":"#6750A4"}); st.rerun()
    for subject in st.session_state.subjects:
        with st.container(border=True):
            info, action = st.columns([5, 1]); info.subheader(subject["name"]); info.caption(f"{subject['professor']} · {subject['hours']}h · {subject['period']} · {progress(subject['id'])}% concluído"); info.write(subject["description"])
            if action.button("Excluir", key=f"delete-subject-{subject['id']}"):
                st.session_state.tasks = [t for t in st.session_state.tasks if t["subject_id"] != subject["id"]]; st.session_state.subjects = [s for s in st.session_state.subjects if s["id"] != subject["id"]]; st.rerun()


def page_tasks():
    st.title("Tarefas")
    if not st.session_state.subjects: st.info("Crie uma disciplina antes de adicionar tarefas."); return
    with st.expander("+ Adicionar tarefa"):
        with st.form("new_task", clear_on_submit=True):
            title = st.text_input("Título"); subject = st.selectbox("Disciplina", st.session_state.subjects, format_func=lambda s:s["name"])
            due, status = st.date_input("Prazo", date.today() + timedelta(days=3)), st.selectbox("Status", ["Pendente", "Em andamento", "Concluída"])
            description = st.text_area("Descrição")
            if st.form_submit_button("Salvar tarefa", type="primary") and title.strip(): st.session_state.tasks.append({"id":str(uuid4()), "subject_id":subject["id"], "title":title.strip(), "description":description.strip(), "due":due, "status":status}); st.rerun()
    selected = st.radio("Filtrar", ["Todas", "Pendentes", "Em andamento", "Concluídas"], horizontal=True); filter_map = {"Pendentes":"Pendente", "Em andamento":"Em andamento", "Concluídas":"Concluída"}
    for task in sorted(st.session_state.tasks, key=lambda t:t["due"]):
        if selected != "Todas" and task["status"] != filter_map[selected]: continue
        with st.container(border=True):
            info, controls = st.columns([4, 2]); info.subheader(task["title"]); info.caption(f"{subject_name(task['subject_id'])} · Prazo: {task['due'].strftime('%d/%m/%Y')}"); info.write(task["description"])
            index = st.session_state.tasks.index(task); statuses = ["Pendente", "Em andamento", "Concluída"]
            status = controls.selectbox("Status", statuses, index=statuses.index(task["status"]), key=f"status-{task['id']}", label_visibility="collapsed")
            if status != task["status"]: st.session_state.tasks[index]["status"] = status; st.rerun()
            if controls.button("Excluir tarefa", key=f"delete-task-{task['id']}"): st.session_state.tasks.pop(index); st.rerun()


def page_insights():
    st.title("Insights")
    pending = [t for t in st.session_state.tasks if t["status"] != "Concluída"]; overdue = [t for t in pending if t["due"] < date.today()]; urgent = [t for t in pending if 0 <= (t["due"] - date.today()).days <= 3]
    if overdue: st.markdown(f"<div class='insight'>⚠️ <b>{len(overdue)} tarefa(s) está(ão) atrasada(s).</b> Comece por <b>{overdue[0]['title']}</b>, de {subject_name(overdue[0]['subject_id'])}.</div>", unsafe_allow_html=True)
    if urgent: st.markdown(f"<div class='insight'>🗓️ Você tem <b>{len(urgent)} entrega(s) nos próximos três dias</b>. Reserve um bloco de estudo ainda hoje.</div>", unsafe_allow_html=True)
    at_risk = sorted(st.session_state.subjects, key=lambda s:progress(s["id"]))
    if at_risk: st.markdown(f"<div class='insight'>🎯 <b>{at_risk[0]['name']}</b> está com {progress(at_risk[0]['id'])}% de progresso. Concluir uma tarefa dessa disciplina melhora seu ritmo geral.</div>", unsafe_allow_html=True)
    if not overdue and not urgent: st.success("Seu planejamento está em dia. Mantenha a consistência!")
    st.caption("Os insights são regras locais de demonstração. Em produção, dados persistidos e métricas Python poderão gerar recomendações mais precisas.")


initialise(); inject_style()
with st.sidebar:
    st.title("🎓 EduTrack AI"); st.caption("Organize. Evolua. Conquiste.")
    section = st.radio("Navegação", ["Dashboard", "Disciplinas", "Tarefas", "Insights"], label_visibility="collapsed")
    st.divider(); st.session_state.theme = st.selectbox("Tema", ["Claro", "Escuro"], index=0 if st.session_state.theme == "Claro" else 1)
    if st.button("Restaurar dados de exemplo", use_container_width=True): st.session_state.subjects, st.session_state.tasks = seed_data(); st.rerun()
{"Dashboard":page_dashboard, "Disciplinas":page_subjects, "Tarefas":page_tasks, "Insights":page_insights}[section]()
