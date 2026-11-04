# Deployment Decisions — Pending

The application is local-first. No hosting platform has been selected.

Before a public/cloud deployment, the product owner must decide:

1. Hosting platform for React frontend and FastAPI backend.
2. Production MongoDB provider and connection/security model.
3. Authentication/access control (required before public exposure).
4. Domain, HTTPS, CORS, and allowed origins.
5. Backup, restore, retention, and monitoring strategy.
6. Expected monthly usage and infrastructure budget.

## Non-negotiable constraints

- Do not point a cloud backend at `mongodb://127.0.0.1:27017`.
- Do not expose the local MongoDB port to the internet.
- Do not deploy the no-auth demo publicly.
- Do not provision paid infrastructure without explicit approval.
- Keep API keys in server-side secret storage/environment variables.
