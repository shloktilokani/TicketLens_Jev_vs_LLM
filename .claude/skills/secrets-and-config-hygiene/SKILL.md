---
name: secrets-and-config-hygiene
description: "Keeps config and secrets on one typed path: required-with-no-default secrets, platform references, loud failure, no stray env reads. Use when touching config, env vars, .env files, or secrets."
metadata:
  title: "Secrets & Config Hygiene"
  category: "Process & Governance"
  tier: practice
  trigger_keywords: "config module, environment variable, env var, .env file, secrets handling, secret manager, api key in config, settings class, missing env var, config drift, rotate leaked key"
---

## Role Identity

Owns *where configuration and secrets are allowed to live and how code is allowed to read them*. It is narrower than `codebase-security-auditor` (the always-on guard against any sensitive data leaving the machine) and more structural than any provider-specific secrets skill (e.g. `gcp-secret-manager`, which owns the mechanics of one backend). This skill's question is: *is there exactly one honest, typed, auditable path from "a value exists somewhere" to "code uses it"?*

## Responsibilities

- **Route configuration through one module.** A single typed settings object (e.g. a `pydantic-settings` class, a `config` package, a typed `ConfigService`) is the only code that reads the process environment. Every other module imports settings from it.
- **Audit the claim, don't repeat it.** If a config module's docstring says "this is the only place that reads the environment," verify it (`grep` for `os.getenv`, `os.environ`, `process.env`, `System.getenv`, `ENV[`) before believing it. Record every violation found; either route it through the settings module or note explicitly that it was seen and deliberately left. Never add a new violation, and never copy an untrue claim forward.
- **Classify every new value on arrival.** Credential-shaped values (passwords, API keys, tokens, signing keys, connection strings with secrets) are **required with no default** so startup fails when they're missing. Operational values (timeouts, pool sizes, feature toggles) get sensible defaults. Make the classification an explicit decision each time a value is added.
- **Watch out for permissive loaders.** Settings loaders configured to ignore unknown keys will silently accept a typo'd variable name and fall back to the default. Don't rely on the loader to catch misspellings — add the new variable to the example env file and to deploy manifests in the same change.
- **Keep secrets out of plain manifest values.** In deploy manifests, secrets use the platform's secret-reference mechanism (e.g. `secretKeyRef`, a secrets annotation, parameter-store references, sealed secrets), never a plain `value:`. Template-substitution steps in CI (e.g. `sed`-style placeholder replacement) are for non-sensitive values only.
- **Fail loudly on a missing or unreadable secret.** A fetch that silently falls back to an empty or stale value is a security regression waiting to surface as a confusing production incident.
- **Decide the authoritative source per environment, once.** For each secret: is it injected by the platform, fetched by the application from a secret manager, or read from a local env file (dev only)? Two paths silently disagreeing about which wins is a defect.
- **Provide one sanctioned test bypass.** Unit tests shouldn't need network access or real credentials. A single explicit flag (e.g. `SKIP_SECRET_FETCH_FOR_TESTS=true`, set in the test bootstrap) that short-circuits secret fetching is legitimate; ad-hoc bypasses scattered through code are not.
- **Recognise the legitimate bootstrap-before-import pattern.** Test bootstraps and one-off generator scripts that set environment values *before* importing application modules are a deliberate, documented pattern — don't "fix" them into the settings module.
- **After a leak, move the secret to a managed store.** When a credential in a local env file leaks, rotate it first (deleting it in a later commit does not un-expose it), move it to the secret manager, fetch it there unconditionally, and use that migration as the template for the project's other secrets.
- **Keep env files out of version control** (`.env`, `.env.*` in `.gitignore`), with a committed `.env.example` listing every variable and no real values. In `.env.example`, never put an inline comment after an empty value (`API_KEY= # your key`): many dotenv parsers read the comment as the value, so put comments on their own line.
- **Confirm a value loaded without revealing it**: print its length or a boolean (`bool(settings.api_key)`), never the value or a prefix of it.

## Technical Skill Set

- Typed settings libraries: `pydantic-settings`, `dynaconf`, `environs` (Python); `zod`/`envalid`/`@nestjs/config` (Node/TS); Spring `@ConfigurationProperties` (Java); `viper`/`envconfig` (Go); `dotenv` loaders across ecosystems.
- Secret stores: cloud secret managers (GCP Secret Manager, AWS Secrets Manager/SSM Parameter Store, Azure Key Vault), HashiCorp Vault, Kubernetes Secrets with sealed-secrets/external-secrets operators.
- Platform injection: Kubernetes/Knative `secretKeyRef`, ECS task-definition secrets, platform secret annotations.
- Secret scanning: gitleaks, trufflehog, detect-secrets — in pre-commit and CI.

## Decision-Making Lens

Optimises for **one honest path and loud failure**. When convenience ("just read it from the env here") conflicts with the single-path rule, the single path wins. When resilience ("fall back to the env value if the fetch fails") conflicts with correctness, correctness wins — a missing secret should stop startup, not degrade silently.

## Trigger Signals

- **Keywords**: env var, `.env`, config, settings, secret, API key, credentials, connection string, rotate, leaked key, missing config.
- **File/path signals**: the settings/config module; `.env*` files; `.env.example`; deploy manifests' env blocks; CI substitution steps; any file calling `os.getenv`/`process.env`/equivalent directly; test bootstraps (`conftest.py`, `setupTests.*`).
- **Project-context signals**: a secret-manager SDK in dependencies; secrets referenced in deploy manifests; a new configuration value being introduced by a feature.

## Collaboration Behavior

- **Always alongside `codebase-security-auditor`** when an actual secret value is involved — that skill's no-egress mandate outranks everything here.
- **Hands off provider mechanics** to the relevant backend skill (e.g. `gcp-secret-manager`) — this skill decides *where a value should come from*, that skill decides *how to fetch it*.
- **Parallel with `devops-engineer` / `deployment-strategy`** on manifest env wiring.
- **Parallel with `dependency-data-risk-audit`** when a new dependency needs its own credential.

## Output Style / Conventions

- Lists each config value touched with: name, required/defaulted, secret or not, authoritative source per environment.
- Reports direct environment reads found outside the settings module as a table (file:line, variable, disposition).
- Verifies a secret loaded by checking presence/length only — never prints the value.

## Anti-Patterns

- Reading the environment directly from arbitrary modules.
- Defaults for credential-shaped values.
- Secret values in plain manifest fields or CI substitution placeholders.
- Silent fallback to an env value when a secret-manager fetch fails.
- Printing, logging, or echoing a secret to "check it loaded."
- Repeating a config module's "single source" claim without verifying it.
- Committing a real `.env` file.

## Stack Detection & Adaptation

Find the settings module (or its absence), the loader library and its unknown-key behaviour, every env file and example file, the deploy manifests' env sections, the CI steps that template values, and any secret-manager SDK in the dependency manifest. Apply this skill's rules through those existing mechanisms; where there's no settings module at all, propose the idiomatic typed-settings library for the detected language rather than hand-rolling one.
