# MedTrack

Aplicativo para organização e acompanhamento da rotina de medicamentos. O MedTrack **não diagnostica, prescreve nem recomenda mudanças de tratamento**; seus índices e insights refletem somente registros feitos pelo usuário.

## Recursos

- Cadastro seguro de conta e autenticação JWT; senhas protegidas com PBKDF2.
- Medicamentos, horários, estoque, doses pendentes/tomadas/atrasadas/ignoradas.
- Dashboard, histórico filtrável, adesão e insights descritivos da rotina.
- Dados fictícios opcionais para apresentação.
- Vinculação explícita ao Telegram por código temporário e webhook.
- Modo cuidador somente para alertas, sem permissão de edição.
- API FastAPI documentada automaticamente em `/docs`.

## Execução local

1. Instale Python 3.11 ou mais recente.
2. Na pasta do projeto, crie o ambiente virtual: `python -m venv .venv`.
3. Ative-o no PowerShell: `.venv\Scripts\Activate.ps1` (Linux/macOS: `source .venv/bin/activate`).
4. Instale: `pip install -r requirements.txt`.
5. Copie `.env.example` para `.env`, defina uma `SECRET_KEY` longa e, se desejar, `TELEGRAM_BOT_TOKEN`.
6. Execute `python backend/main.py` ou `uvicorn backend.main:app --reload`.
7. Abra `http://localhost:pythonpythop8000`. O SQLite e suas tabelas são criados automaticamente na primeira inicialização.

O frontend é servido pelo próprio FastAPI, portanto não exige outro servidor. Para uma apresentação, crie uma conta e use **carregar dados fictícios** no dashboard vazio.

## Telegram

Crie um bot no BotFather, configure `TELEGRAM_BOT_TOKEN` apenas no backend e exponha `/api/telegram/webhook` por HTTPS. Registre a URL com o método `setWebhook` da Telegram Bot API. No app, o usuário solicita um código temporário e o envia ao bot; mensagens só são enviadas depois dessa confirmação. `APP_BASE_URL` deve ser a URL pública.

Para lembretes locais, um agendador externo pode chamar `POST /api/cron/notifications` periodicamente. Defina `CRON_SECRET` e envie `Authorization: Bearer <segredo>`.

## Publicação na Vercel

1. Envie o repositório à Vercel; `vercel.json` direciona a API Python e os arquivos estáticos.
2. Configure `DATABASE_URL`, `SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `APP_BASE_URL` e `CRON_SECRET` no painel.
3. Use PostgreSQL/Supabase em produção: o SQLite da Vercel é efêmero e não oferece persistência confiável. O SQLAlchemy já aceita uma URL PostgreSQL (`postgresql+psycopg://...`).
4. No plano Hobby, configure cron-job.org, GitHub Actions ou outro agendador HTTP para chamar `POST /api/cron/notifications` a cada 10 minutos, enviando `Authorization: Bearer <CRON_SECRET>`. O plano Hobby da Vercel aceita apenas execuções diárias; no plano Pro, você pode adicionar o agendamento `*/10 * * * *` ao `vercel.json`. Não há processo Python contínuo.

Observação: o `CRON_SECRET` nativo da Vercel é enviado como Bearer automaticamente. Verifique os limites do plano escolhido. Para alto volume, separe a fila de notificações em um serviço próprio.

## Endpoints principais

Contas: `POST /api/users`, `POST /api/login`, `GET /api/me`. Medicamentos: `GET/POST /api/medications`, `PUT/DELETE /api/medications/{id}`. Doses: `GET /api/doses`, `POST /api/doses/{id}/taken`, `POST /api/doses/{id}/snooze`. Relatórios: `GET /api/history`, `GET /api/adherence`, `GET /api/insights`. Integrações: `POST /api/telegram/connect`, `POST /api/telegram/webhook`, `GET/POST /api/caregiver`.

## Segurança

Nunca confirme `.env` ou tokens reais no controle de versão. Configure CORS para os domínios usados e troque a chave de desenvolvimento. Em produção, habilite HTTPS e considere rate limiting no login e validação do segredo de webhook do Telegram.
