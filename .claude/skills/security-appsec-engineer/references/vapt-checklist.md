# VAPT checklist (OWASP Top 10 2025, mapped to CWE)

Standing checks for every change that adds or touches an endpoint, a query, a template, auth/session
code, or an error handler. Each item is phrased stack-neutrally; short framework examples follow where
the idiom matters. Every item that can be asserted automatically belongs in the project's
security-posture test (see `../SKILL.md`).

## A01:2025 Broken Access Control — CWE-284, CWE-862, CWE-639, CWE-352

- [ ] **Default deny.** A new route is authenticated unless it is explicitly listed as public (static
      assets, health check, login). Public routes are an allow-list, never the fallback.
- [ ] **Role checks on mutations.** Every state-changing or administrative operation (data refresh,
      cache flush, sync trigger, user management, management/actuator endpoints) requires an explicit
      privileged role, enforced server-side in one central place or by method-level annotation.
- [ ] **Object-level authorisation (IDOR).** Any client-supplied record/user/tenant ID is checked against
      the authenticated caller before read or write. Hiding the ID in the UI is not a control.
- [ ] **CSRF on every state-changing verb** (`POST`/`PUT`/`PATCH`/`DELETE`) for cookie-authenticated
      apps. Prefer the framework's token mechanism (synchronizer or masked double-submit cookie); never
      disable it globally to make one client work.
- [ ] **Account/domain allow-lists** (when sign-in is restricted to an organisation's identity domain or a
      list of addresses) are enforced server-side after the identity provider returns, and are
      configuration, not code.
- [ ] **SSRF:** server-side fetches of user-supplied URLs go through a host allow-list and block
      internal/metadata address ranges (CWE-918).

```java
// Spring Security: default deny, explicit public list, admin-only mutations
http.authorizeHttpRequests(a -> a
    .requestMatchers("/health", "/login", "/assets/**").permitAll()
    .requestMatchers(HttpMethod.POST, "/admin/**").hasRole("ADMIN")
    .anyRequest().authenticated());
```

## A02:2025 Security Misconfiguration — CWE-693, CWE-1021, CWE-16

- [ ] **Security headers present on every response:** `Content-Security-Policy` (strict; see the
      `csp-strict-frontend` skill), `X-Frame-Options: DENY` plus `frame-ancestors 'none'`,
      `X-Content-Type-Options: nosniff`, `Strict-Transport-Security` (production), `Referrer-Policy`.
- [ ] **`TRACE`/`TRACK` disabled** and unexpected verbs answered with `405`. Check the container/proxy
      too, not only the app router.
- [ ] **CORS is an explicit origin allow-list**, never `*` with credentials. Verify it from a real
      browser (see `../SKILL.md`).
- [ ] **No debug/management surface exposed** in production (debug toolbars, unauthenticated
      actuator/admin endpoints, directory listings, default credentials).

```js
// Express: headers + method control
app.use(helmet({ frameguard: { action: "deny" } }));
app.use((req, res, next) => ["TRACE", "TRACK"].includes(req.method) ? res.sendStatus(405) : next());
```

## A03:2025 Software Supply Chain Failures — CWE-1395, CWE-1104

- [ ] Dependencies scanned for known CVEs on every change to a manifest/lockfile; see
      `dependency-vulnerability-scan.md`.
- [ ] New libraries go through `dependency-data-risk-audit` before they are added.

## A04:2025 Cryptographic Failures — CWE-916, CWE-798, CWE-319

- [ ] **Passwords hashed with an adaptive algorithm and a stated work factor** (bcrypt cost >= 12, or
      Argon2id / scrypt with current recommended parameters). Never a fast hash, never reversible
      encryption.
- [ ] **No hardcoded secrets or credentials** in code, config, tests, or fixtures; production secrets
      come from a secret manager (see `secrets-and-config-hygiene`).
- [ ] TLS for every hop that leaves the host; HSTS in production.

## A05:2025 Injection — CWE-89, CWE-79, CWE-78

- [ ] **Parameterised queries only.** No string concatenation or formatting into SQL, including table
      and column names.
- [ ] **`ORDER BY`, sort direction, column and table identifiers cannot be parameterised**, so they come
      from a server-side allow-list map (`{"name": "customer_name", ...}`); reject anything else.
- [ ] **No raw HTML injection sinks with user-controlled data:** `dangerouslySetInnerHTML`,
      `innerHTML`/`outerHTML`, `v-html`, `|safe`/`mark_safe`, `th:utext`, `<%- %>`. If HTML must be
      rendered, sanitise with a vetted library on the server and again before the sink.
- [ ] Shell/OS commands never built from user input; use argument arrays.

```python
# Django/Python: allow-listed ORDER BY with a parameterised WHERE
SORTS = {"name": "customer_name", "created": "created_at"}
col = SORTS.get(sort_key, "created_at")
direction = "DESC" if desc else "ASC"
cursor.execute(f"SELECT id, customer_name FROM customers WHERE region = %s ORDER BY {col} {direction}", [region])
```

## A06:2025 Insecure Design — CWE-770, CWE-400

- [ ] **Rate limits on all API endpoints** (tighter on auth and expensive endpoints) to stop grinding,
      scraping, and resource exhaustion.
- [ ] **Hard upper bounds** on upload size, rows per batch/export, and memory for file or spreadsheet
      processing.
- [ ] Abuse cases from the threat model have negative tests.

## A07:2025 Authentication Failures — CWE-384, CWE-307, CWE-614, CWE-1004, CWE-1275

- [ ] **Session cookie flags:** `HttpOnly`, `Secure` (production), `SameSite=Strict` or `Lax`, `Path=/`,
      and a non-default cookie name that does not reveal the stack.
- [ ] **Session ID rotated on login** (and on privilege change) to prevent fixation.
- [ ] **Login lockout / progressive back-off** after repeated failures, keyed on account and source, with
      a generic failure message that does not reveal whether the account exists.
- [ ] Concurrent-session limits and server-side logout/revocation where the risk warrants them.

```java
// Spring: rotate session ID on authentication
http.sessionManagement(s -> s.sessionFixation(f -> f.changeSessionId()).maximumSessions(3));
```
```python
# Django: SESSION_COOKIE_HTTPONLY/SECURE/SAMESITE settings; login() already cycles the session key
SESSION_COOKIE_SECURE = True; SESSION_COOKIE_SAMESITE = "Strict"; CSRF_COOKIE_SECURE = True
```

## A08:2025 Software or Data Integrity Failures — CWE-494, CWE-502

- [ ] No deserialisation of untrusted data into arbitrary types; third-party scripts pinned with
      Subresource Integrity or self-hosted.

## A09:2025 Security Logging and Alerting Failures — CWE-532, CWE-117, CWE-778

- [ ] **Log hygiene:** never log passwords, tokens, session IDs, full credentials, or PII; use the
      project's standard logger (see `logging-standards`), not ad-hoc prints.
- [ ] User-controlled values are encoded/escaped before they reach a log line (log injection).
- [ ] Auth failures, lockouts, authorisation denials, and admin actions are logged with enough context to
      investigate.

## A10:2025 Mishandling of Exceptional Conditions — CWE-209, CWE-755

- [ ] **Uniform error body:** every handled error returns one consistent structure (e.g. RFC 9457
      problem details) with a generic message and an **opaque reference ID** that is also written to the
      server log with the full detail.
- [ ] **No stack traces, SQL errors, class names, file paths, or schema details** reach the client in
      production, including from the framework's default error page.
- [ ] Failures fail closed: an exception in an auth or validation path denies, never allows.

## Before the change is done

- [ ] The security-posture test passes, and any new endpoint or control has its assertion there.
- [ ] The endpoint inventory is updated in the same change.
- [ ] Frontend builds with no new unsafe escape hatches (raw-HTML sinks, CSP relaxations, disabled lint
      rules).
