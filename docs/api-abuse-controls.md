# P5 — Limites de solicitações e avaliações

## Política inicial

| Operação | Configuração | Padrão | Chave |
| --- | --- | --- | --- |
| Login | `AUTH_LOGIN_REQUESTS_PER_MINUTE` | 20 por 60 segundos | Origem ASGI |
| Recuperação | `AUTH_RESET_REQUESTS_PER_15_MINUTES` | 5 por 900 segundos | Origem ASGI |
| Chat + perguntas/avaliações de revisão | `EDU_AI_REQUESTS_PER_MINUTE` / `EDU_AI_REQUESTS_PER_DAY` | 5 por 60 segundos / 50 por 24 horas | Usuário autenticado |

Todos os limites aceitam inteiros de 1 a 1000. Janelas são móveis, não viradas de
relógio. Vinte logins/minuto permitem erros de digitação e uma pequena origem
compartilhada sem permitir tentativas ilimitadas. Cinco recuperações/15 minutos
permitem repetir uma solicitação quando o e-mail demora; recuperação não deveria
ser uma operação contínua. Os valores devem ser revistos conforme o uso real em
redes de faculdade com NAT. Não há bloqueio por e-mail: conhecer um endereço não
permite impedir logins dessa conta vindos de outra origem.

O orçamento Gemini existente de 5/minuto e 50/dia foi mantido. Uma revisão normal
consome no máximo duas reservas (perguntas + avaliação), deixando espaço para o
chat; o limite diário equivale a 25 revisões completas sem chat. Não é uma cota
financeira global do projeto Gemini.

Login e recuperação contam requisições com payload válido antes de consultar a
conta, com sucesso ou falha, inclusive SMTP indisponível. Payloads rejeitados pela
validação FastAPI (422) não consomem esse orçamento. E-mail existente e inexistente
recebem a mesma política. Excesso retorna 429 e `Retry-After` em segundos, sem
e-mail ou motivo relacionado à existência da conta. Tentativas recusadas não
prolongam a janela. O limitador não registra valores pessoais ou credenciais.

## Reutilização e limites operacionais

`app/services/request_budget.py` centraliza `ensure_request_budget()` antes
presente na rota do chat. A contagem persistente de mensagens do chat continua
como piso de proteção. A reserva atômica em memória também cobre revisões,
requisições simultâneas e falhas do provedor, antes da chamada externa.

O mesmo componente de janelas é utilizado para autenticação; a contagem de
mensagens do banco não servia para operações anônimas. Não foram adicionados
Redis, filas, dependências ou tabelas.

- Contadores em memória se perdem ao reiniciar. Mensagens de chat ainda presentes
  no banco continuam sujeitas à verificação persistente; reservas de revisão não.
- Workers e instâncias **não compartilham** esses contadores. A contagem de chat
  no banco não é uma reserva distribuída e pode sofrer concorrência.
- Há no máximo 2048 chaves por processo, com HMAC e sal efêmero, sem IPs/IDs em
  texto. Cada chave retém no máximo a quota aplicável (até 1000 timestamps).
  Entradas expiradas são reutilizadas/removidas quando acessadas ou sob pressão.
- Ao atingir a capacidade, novas chaves recebem 429 até haver espaço; contadores
  ativos não são descartados. Isso limita memória, mas um ataque com muitas
  origens pode causar indisponibilidade temporária para novas origens.
- Reiniciar, alternar instâncias ou usar várias origens pode ampliar o orçamento.
  Para múltiplos workers, escalabilidade horizontal, ataques distribuídos ou
  proteção financeira global, é necessário um orçamento atômico compartilhado
  e/ou controle no gateway, além das quotas do provedor.

Não existe proteção global contra abuso nesta versão. Os testes usam uma nova
instância do limitador por teste, sem desabilitar regras em `ENVIRONMENT=test`.

## Proxy e hospedagem

A aplicação usa somente `request.client.host` do ASGI, nunca lê diretamente
`X-Forwarded-For`, `Forwarded` ou `X-Real-IP`. O Uvicorn pode transformar o peer
ASGI antes de a aplicação recebê-lo. Configure `--forwarded-allow-ips` ou
`FORWARDED_ALLOW_IPS` somente com IPs/redes de proxies controlados que sobrescrevam
os cabeçalhos. Não use `*` em uma aplicação acessível diretamente. Sem proxy
confiável, use `--no-proxy-headers`; clientes podem então compartilhar o limite
do IP do gateway. Não invente faixas de confiança do Render: confirme a topologia
do serviço antes de configurar. O blueprint atual não fixa essa confiança e não
define múltiplos workers; a configuração efetiva da hospedagem não foi auditada.

## Revisões e preservação

Início e submissão consultam a revisão do usuário com `FOR UPDATE OF
review_missions NOWAIT`, atualizando o estado carregado na sessão. Disputa de
lock PostgreSQL retorna 409 com espera de 1 segundo. O lock permanece durante
a chamada externa até commit/rollback. Isso impede submissões simultâneas da
mesma missão em diferentes workers que usem o mesmo PostgreSQL, mas mantém uma
conexão ocupada durante a chamada Gemini.

Revisões concluídas retornam o resultado salvo (200), ignorando novas respostas,
sem reavaliação nem consumo de orçamento. Perguntas existentes são reutilizadas.
Submissão exige estado `in_progress`, perguntas e data disponível. Cada resposta
aceita até 4000 caracteres para limitar o conteúdo enviado ao modelo.

Falha Gemini mantém o comportamento honesto: respostas são salvas, revisão é
concluída e a nota fica nula, com aviso de que não houve avaliação. Uma repetição
não tenta cobrar uma nova avaliação. Se o orçamento estiver esgotado, retorna
429 antes da avaliação e da persistência das novas respostas; elas precisam ser
reenviadas depois da espera.

Não há garantia de exatamente uma cobrança se o processo cair ou o commit falhar
depois de o provedor aceitar a chamada. Nenhum controle local pode desfazer esse
consumo externo. Os testes locais validam concorrência do limitador, simulação
de disputa de lock e SQL PostgreSQL compilado; não substituem testes concorrentes
em PostgreSQL autorizado. SMTP/Gemini reais não são chamados nos testes novos.

## Validação integrada P4 + P5

`tests/integration/test_review_concurrency.py` roda exclusivamente no serviço
PostgreSQL descartável do GitHub Actions. A fixture normal mantém todas as
validações P1, incluindo identidade e marca do banco. Localmente esses três
testes são ignorados antes de preparar o banco.

O teste de concorrência pausa um Gemini simulado e usa sessões independentes:
confere que uma segunda submissão recebe 409 em até dois segundos, outro usuário
recebe 404 e leitores não enxergam resultados parciais. Uma tentativa explícita
de `FOR UPDATE NOWAIT` verifica que o lock permanece durante a espera externa.
Depois do commit, o lock é liberado e repetições não alteram nota nem respostas.
Outros testes verificam falha do provedor e rollback depois de flush, antes do
commit. Todos usam Gemini simulado, sem chamadas externas ou cobrança.

O cliente Gemini atual usa timeout HTTP de 30 segundos por operação, não um
deadline total. Uma resposta lenta ocupa uma conexão e mantém o lock da missão;
rotas comuns de edição/exclusão que não usam NOWAIT também podem esperar por ela.
O teste comprova ausência de espera prolongada entre submissões concorrentes,
não ausência universal de deadlocks sob qualquer carga.

Melhoria mínima proposta para uma próxima alteração: um timeout específico e
mais curto para avaliações (por exemplo, 10 segundos, após observar latência),
mantendo o fallback sem nota fictícia e o lock até persistir as respostas. Um
deadline total requer controle adicional; reduzir timeout por operação não é
equivalente. Não se deve liberar o lock antes do Gemini sem persistir uma reserva
de processamento e tratar sua recuperação. Essa mudança de arquitetura não foi
introduzida apenas para fazer os testes passarem.
