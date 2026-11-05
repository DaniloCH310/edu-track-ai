# Graph Report - edu-track-ai  (2026-11-05)

## Corpus Check
- 138 files · ~305,732 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 24 file(s) not represented in the graph (top: .css 13, .cmd 4, .example 2)

## Summary
- 1038 nodes · 2709 edges · 61 communities (34 shown, 27 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 277 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `47db65a8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AcademicTask
- ClassroomRepository
- test_classroom_integration.py
- api/review_missions.py
- get_db
- api/classroom.py
- agenda.js
- api/edu_ia.py
- EduTrack — roteiro da Avaliação Parcial 02
- api/subjects.py
- main.py
- app.js
- security.py
- tasks.js
- subjects.js
- RegisterInput
- dashboard.js
- dependencies.py
- test_auth_flow.py
- EduTrack application shell
- ui.js
- OpenSpec baseline implementation plan
- test_auth.py
- app.py
- test_password_reset.py
- Graph-first repository navigation
- Tabelas
- ApiError
- state.js
- Purple calendar with completion check illustration
- Isometric landscaped campus with a student at its center
- Isometric learning islands with connected study milestones
- weekly-review.js
- Render production deployment
- test_health_returns_ok
- edutrack-ai
- EmailService
- User
- config.py
- conftest.py
- api/auth.py
- oauth.py
- test_classroom_crypto.py
- EduTrack — comparação com os requisitos da disciplina

## God Nodes (most connected - your core abstractions)
1. `AcademicTask` - 79 edges
2. `Subject` - 72 edges
3. `get_db()` - 39 edges
4. `TaskStatus` - 34 edges
5. `get_settings()` - 31 edges
6. `User` - 30 edges
7. `ClassroomRepository` - 29 edges
8. `ApiError` - 27 edges
9. `ClassroomSyncService` - 24 edges
10. `TaskRepository` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Entidades complementares` --references--> `TimestampMixin`  [INFERRED]
  docs/roteiro-avaliacao-parcial-02.md → app/models/base.py
- `8. Excluir e comprovar o CRUD completo — 1 minuto` --references--> `delete_task()`  [INFERRED]
  docs/roteiro-avaliacao-parcial-02.md → app/api/tasks.py
- `Arquivos para deixar abertos, nesta ordem` --references--> `create_app()`  [INFERRED]
  docs/roteiro-avaliacao-parcial-02.md → app/main.py
- `Arquivos para deixar abertos, nesta ordem` --references--> `User`  [INFERRED]
  docs/roteiro-avaliacao-parcial-02.md → app/models/user.py
- `Matriz das 16 tarefas` --references--> `percentage()`  [INFERRED]
  docs/auditoria-classroom-2026-10-27.md → app/services/dashboard.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Production deployment validation and operations** — _github_workflows_ci_continuous_verification, docs_production_render_and_supabase_production_runbook, docs_superpowers_plans_2026_08_31_publicacao_producao_production_publication_implementation_plan [EXTRACTED 1.00]
- **Optional external integrations preserve local application operation and secret isolation** — docs_superpowers_specs_2026_09_03_google_classroom_integration_design_document, openspec_specs_edu_ai_tutor_spec_document, openspec_specs_google_classroom_integration_spec_document [INFERRED 0.85]
- **Shared task completion and academic progress** — app_static_index_edutrack_application_shell, design_qa_learning_campus_design_verification, docs_superpowers_plans_2026_08_31_agenda_semanal_weekly_agenda_implementation_plan, docs_superpowers_plans_2026_08_31_plano_estudo_inteligente_explainable_study_recommendation_plan [INFERRED 0.95]
- **Shared user-owned task state drives Campus, agenda and academic organization** — openspec_specs_academic_organization_spec_document, openspec_specs_campus_dashboard_spec_document, openspec_specs_weekly_agenda_and_study_plan_spec_document [INFERRED 0.95]

## Communities (61 total, 27 thin omitted)

### Community 0 - "AcademicTask"
Cohesion: 0.06
Nodes (57): Base, map_submission_status(), TimestampMixin, utc_now(), ClassroomConnection, ClassroomCourseLink, ClassroomTaskLink, Subject (+49 more)

### Community 1 - "ClassroomRepository"
Cohesion: 0.09
Nodes (18): ClassroomGateway, ClassroomSyncService, ClassroomRepository, ClassroomSyncResult, test_classroom_subject_exposes_only_safe_source(), login(), make_subject(), task_payload() (+10 more)

### Community 2 - "test_classroom_integration.py"
Cohesion: 0.07
Nodes (20): GoogleClassroomClient, GoogleClassroomError, GoogleTokens, authenticate(), configure_classroom(), connect(), FakeGoogleClient, test_authorize_sets_http_only_context_cookie_and_redirects() (+12 more)

### Community 3 - "api/review_missions.py"
Cohesion: 0.07
Nodes (25): dashboard(), edu_ai_client(), get_owned_mission(), list_review_missions(), output(), start_review_mission(), submit_review_mission(), GeminiClient (+17 more)

### Community 4 - "get_db"
Cohesion: 0.09
Nodes (19): create_task(), delete_task(), ensure_owned_subject(), get_owned_task(), get_task(), list_tasks(), task_not_found(), update_task() (+11 more)

### Community 5 - "api/classroom.py"
Cohesion: 0.19
Nodes (10): authorize(), callback(), classroom_status(), disconnect_classroom(), get_classroom_client(), _redirect(), sync_classroom(), get_settings() (+2 more)

### Community 6 - "agenda.js"
Cohesion: 0.08
Nodes (41): bindAgendaInteractions(), changeAgendaWeek(), daysOfWeek(), fullDateFormatter, isOverdue(), labels, localDate(), missionMarkup() (+33 more)

### Community 7 - "api/edu_ia.py"
Cohesion: 0.13
Nodes (22): create_conversation(), create_message(), delete_conversation(), edu_ia_status(), ensure_request_budget(), get_conversation(), get_edu_ai_client(), get_owned_conversation() (+14 more)

### Community 8 - "EduTrack — roteiro da Avaliação Parcial 02"
Cohesion: 0.20
Nodes (8): Apêndice A — dicionário de dados para consulta, Apêndice B — APIs que demonstram o CRUD, EduTrack — roteiro da Avaliação Parcial 02, Entidades complementares, Núcleo acadêmico, O que será avaliado, Preparação antes da apresentação, Se o tempo cair para 8 minutos

### Community 9 - "api/subjects.py"
Cohesion: 0.08
Nodes (23): create_subject(), delete_subject(), get_owned_subject(), get_subject(), list_subjects(), update_subject(), SubjectRepository, SubjectCreate (+15 more)

### Community 10 - "main.py"
Cohesion: 0.13
Nodes (7): error_payload(), register_error_handlers(), api_error_handler(), unexpected_error_handler(), validation_error_handler(), create_app(), test_validation_errors_use_the_public_error_envelope()

### Community 11 - "app.js"
Cohesion: 0.12
Nodes (15): navigate(), routes, routeTitles, showApp(), chatMarkup(), conversationMarkup(), createConversation(), inlineMarkdown() (+7 more)

### Community 12 - "security.py"
Cohesion: 0.19
Nodes (10): create_access_token(), decode_access_token(), generate_reset_token(), hash_password(), hash_reset_token(), verify_password(), test_access_token_round_trip_preserves_user_id(), test_expired_access_token_is_rejected() (+2 more)

### Community 13 - "tasks.js"
Cohesion: 0.17
Nodes (26): bindTaskActions(), changeStatus(), classroomBadge(), classroomLink(), daysFromToday(), deleteTask(), eduIAButton(), labels (+18 more)

### Community 14 - "subjects.js"
Cohesion: 0.17
Nodes (25): bindDetailActions(), bindSubjectActions(), buildingCard(), buildingZones, campusMarkup(), classroomBadge(), deleteSubject(), detailMarkup() (+17 more)

### Community 15 - "RegisterInput"
Cohesion: 0.14
Nodes (10): ForgotPasswordInput, LoginInput, MessageOutput, RegisterInput, ResetPasswordInput, UserOutput, validate_strong_password(), test_registration_rejects_passwords_missing_a_strength_requirement() (+2 more)

### Community 16 - "dashboard.js"
Cohesion: 0.15
Nodes (22): availabilityControl(), availableMinutes(), bindCampusBuildings(), campusIdentity(), campusLevel(), campusMarkup(), campusMilestones(), campusZones (+14 more)

### Community 18 - "test_auth_flow.py"
Cohesion: 0.05
Nodes (13): live_server(), LiveServer, page(), test_classroom_integration_disconnected_and_connected_states(), classroom_api(), test_edu_ia_creates_a_general_conversation_when_available(), edu_ia_api(), read_project_file() (+5 more)

### Community 19 - "EduTrack application shell"
Cohesion: 0.15
Nodes (10): Continuous verification, EduTrack application shell, Windows installation startup and shutdown, Learning Campus design verification, Render and Supabase production runbook, EduTrack MVP replacement plan, Weekly agenda implementation plan, Explainable study recommendation plan (+2 more)

### Community 21 - "ui.js"
Cohesion: 0.21
Nodes (12): bindDialogControls(), clearErrors(), closeEntityDialog(), confirmAction(), empty(), escapeHtml(), initPasswordToggles(), initTheme() (+4 more)

### Community 22 - "OpenSpec baseline implementation plan"
Cohesion: 0.18
Nodes (17): Google Classroom implementation plan, OpenSpec baseline implementation plan, Weekly agenda design, Deterministic study recommendation, Google Classroom read-only integration design, EDU IA contextual tutor proposal, EDU IA completed implementation checklist, OpenSpec proposed change workflow (+9 more)

### Community 24 - "app.py"
Cohesion: 0.27
Nodes (8): initialise(), page_dashboard(), page_insights(), page_subjects(), page_tasks(), progress(), seed_data(), subject_name()

### Community 25 - "test_password_reset.py"
Cohesion: 0.36
Nodes (6): PasswordResetToken, reset_token_factory(), create_token(), test_expired_reset_token_is_rejected(), test_forgot_password_is_neutral_and_only_emails_known_user(), test_reset_token_is_single_use_and_changes_password()

### Community 27 - "Tabelas"
Cohesion: 0.13
Nodes (14): 10. Vínculos de tarefas Google Classroom, 1. Usuários, 2. Recuperação de senha, 3. Disciplinas, 4. Tarefas acadêmicas, 5. Conversas da EDU IA, 6. Mensagens da EDU IA, 7. Missões de revisão (+6 more)

### Community 30 - "Purple calendar with completion check illustration"
Cohesion: 0.67
Nodes (3): Completed or confirmed scheduled tasks, Purple calendar with completion check illustration, Scheduling and calendar planning

### Community 34 - "Render production deployment"
Cohesion: 0.67
Nodes (3): EduTrack full-stack MVP architecture, Render production deployment, Production dependency installation

### Community 53 - "EmailService"
Cohesion: 0.14
Nodes (3): EmailService, test_password_reset_message_contains_safe_recipient_and_expiring_link(), test_password_reset_uses_starttls_login_and_sends_message()

### Community 54 - "User"
Cohesion: 0.30
Nodes (3): User, UserRepository, AuthService

### Community 55 - "config.py"
Cohesion: 0.18
Nodes (4): Settings, test_production_accepts_secure_settings(), test_production_rejects_insecure_session_cookie(), test_production_rejects_non_https_frontend_url()

### Community 56 - "conftest.py"
Cohesion: 0.27
Nodes (5): client(), database_cleaner(), db_session(), user_factory(), create_user()

### Community 57 - "api/auth.py"
Cohesion: 0.29
Nodes (7): current_user(), forgot_password(), login(), logout(), register(), reset_password(), set_session_cookie()

### Community 58 - "oauth.py"
Cohesion: 0.23
Nodes (6): create_oauth_context(), InvalidOAuthState, OAuthContext, validate_oauth_context(), test_oauth_context_is_bound_to_state_and_user(), test_oauth_context_uses_s256_pkce_and_expires_after_ten_minutes()

### Community 59 - "test_classroom_crypto.py"
Cohesion: 0.38
Nodes (7): decrypt_refresh_token(), encrypt_refresh_token(), _fernet(), settings_values(), test_enabled_classroom_requires_complete_configuration(), test_invalid_fernet_key_is_rejected_without_echoing_it(), test_refresh_token_round_trip_never_returns_plaintext()

### Community 60 - "EduTrack — comparação com os requisitos da disciplina"
Cohesion: 0.22
Nodes (8): EduTrack — comparação com os requisitos da disciplina, Entrega final mais recente, Ferramentas autorizadas e diferenças de escopo, Fontes consultadas, Matriz das 16 tarefas, O que já serve de base para a apresentação, Pendências prioritárias, Resultado

## Knowledge Gaps
- **52 isolated node(s):** `labels`, `weekdayFormatter`, `fullDateFormatter`, `weekStart`, `selectedDate` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 295 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `3. Disciplinas: criar, consultar e editar — 2 minutos` connect `api/subjects.py` to `subjects.js`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Why does `get_db()` connect `get_db` to `AcademicTask`, `api/review_missions.py`, `api/classroom.py`, `api/edu_ia.py`, `api/subjects.py`, `dependencies.py`, `api/auth.py`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `Subject` connect `AcademicTask` to `ClassroomRepository`, `test_classroom_integration.py`, `api/review_missions.py`, `get_db`, `api/subjects.py`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `AcademicTask` (e.g. with `create_task()` and `get_owned_task()`) actually correct?**
  _`AcademicTask` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Subject` (e.g. with `create_subject()` and `get_owned_subject()`) actually correct?**
  _`Subject` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `TaskStatus` (e.g. with `list_tasks()` and `ClassroomSyncService`) actually correct?**
  _`TaskStatus` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `labels`, `weekdayFormatter`, `fullDateFormatter` to the rest of the system?**
  _52 weakly-connected nodes found - possible documentation gaps or missing edges._