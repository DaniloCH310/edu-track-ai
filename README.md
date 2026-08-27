# EduTrack AI

Protótipo responsivo em Streamlit para organizar disciplinas, tarefas e progresso acadêmico.

## Executar localmente

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Funcionalidades

- Dashboard com progresso, prazos e gráficos.
- Cadastro e manutenção de disciplinas.
- Tarefas vinculadas a disciplinas, com prazo e status.
- Insights locais para destacar atrasos e prioridades.
- Tema claro/escuro e layout adequado para telas menores.

Os dados deste protótipo vivem apenas na sessão do navegador. Em uma evolução, as coleções `users`, `subjects` e `academic_tasks` serão persistidas no Xano, e os insights poderão ser calculados por serviços Python.
