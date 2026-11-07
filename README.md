# TicketLens_Jev_vs_LLM

A single-user demonstration application for managing fictional ShopKart customer-support tickets and comparing Jev (TypeSafe AI) with a configurable GPT model on structured ticket-classification tasks.

## Documentation map

- `AGENTS.md` — operating instructions for an autonomous coding agent.
- `.context/code-size-standards.md` — code size and reuse rules, with the research behind them.
- `.context/ROADMAP.md` — plain-language phase order and the steps that need the owner.
- `.context/implementation.md` — sequenced end-to-end build plan, acceptance criteria, and deployment-readiness work.
- `.context/design.md` — frontend UX, page layouts, interaction rules, and visual system.
- `.context/architecture.md` — system boundaries, request flows, provider adapters, and operational decisions.
- `.context/requirements.md` — product scope and functional/non-functional requirements.
- `.context/data-model.md` — MongoDB collections, document shapes, indexes, and deletion behavior.
- `.context/ai-evaluation.md` — shared classification contract, Jev/GPT integration, evaluation methodology, and cost logging.
- `backend/.env.example` — environment-variable template.
- `.context/sample_tickets_template.csv` — CSV import header template.
- `.context/sample_tickets_100.csv` — 100 fictional, labelled ShopKart tickets for evaluation and import.

## Product summary

ShopKart is a fictional Indian e-commerce marketplace. TicketLens lets one operator create or import support tickets, run Jev or GPT independently or together, inspect results side by side, manually choose a final classification, and review historical executions and costs.

## Local-first development

- Frontend: React + Vite + TypeScript
- Styling: Tailwind CSS + shadcn/ui
- Backend: Python + FastAPI
- Database: locally installed MongoDB Community Edition
- AI providers: TypeSafe Jev API and OpenAI API
- No Docker for local development
- No authentication in the initial local single-user version

## Important scope boundary

The initial application is local-first. A locally installed MongoDB instance is not directly reachable by a cloud-hosted backend. Before public/cloud deployment, choose a production hosting target and a reachable production MongoDB deployment (for example, managed MongoDB), and add authentication/access control. Do not expose the local MongoDB service to the public internet.

## Run locally

Requires Python 3.13, Node 22.12 or newer, and MongoDB Community Edition. API keys are needed only for real provider calls.

MongoDB, local only (adjust the paths if MongoDB is installed elsewhere):

```bash
# --fork is not supported on macOS, so run it in the background with nohup.
nohup ~/mongodb-macos-aarch64--9.0.4/bin/mongod --dbpath ~/data/db --bind_ip 127.0.0.1 --port 27017 --logpath ~/data/mongod.log --logappend >/dev/null 2>&1 &
mongosh --quiet --eval 'db.runCommand({ ping: 1 })'   # expect { ok: 1 }
```

Do not start `mongod` with `sudo`: the data folder would become owned by root, and later starts as your user fail.
To stop it: `mongosh admin --quiet --eval 'db.shutdownServer()'`.

Backend, from `backend/` (http://127.0.0.1:8000/docs):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend, from `frontend/` (http://localhost:5173):

```bash
npm install
npm run dev
```

Tests and checks are listed in `CLAUDE.md`. Build status is in `.context/PROGRESS.md`.

## Architecture

See `.context/architecture.md` for system boundaries and request flows, and `.context/data-model.md` for the MongoDB collections.

## Getting started

Read `AGENTS.md` first, then follow `.context/implementation.md` in order. The human operator is responsible for installing MongoDB locally (the coding agent may start it on loopback) and providing API credentials in the backend `.env` file. The coding agent should implement the remaining application without asking for routine product decisions.
