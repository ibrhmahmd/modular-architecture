# Default decisions

Each decision has the rule, why it won, what was rejected, and what enforces it. They come from migrating a real FastAPI + Postgres monolith with eleven modules; the reasons are the failures that system had. A project's own ADRs override any of them (see [reconcile.md](reconcile.md)).

Tier: **L** = part of the *light* tier; everything else is *full* only.

## D1 — Every module has the same layers and owns its HTTP API

```text
<modules>/<name>/
  api/           routers, HTTP request/response schemas, service factories
  services/      business logic, use cases
  repositories/  data access
  schemas/       service DTOs (inputs, results, read models)
  models/        ORM models
  __init__.py    the facade
```

Inside a module, imports point downward only: `api → services → repositories → models`, and `schemas` is importable by all of them. Services never import `api` (so HTTP schemas never reach a service). A shared top-level HTTP package keeps only cross-cutting code: app factory and router registry, middleware, exception handlers, auth guards, the response envelope, the unit-of-work dependency.

- **Why:** one template is predictable for agents and humans. Different shapes per module (vertical slices here, flat files there) each needed their own map, and vertical slices added folders without adding depth.
- **Rejected:** choosing a shape per module by size or entity count; vertical/feature slices with per-slice interface files; HTTP code in a central `routers/` and `schemas/` far from the module.
- **Enforced by:** the in-module layers test (`services` must not import `api`, `repositories` must not import `services`/`api`, `schemas`/`models` import neither).

## D2 — Modules form a fixed order and talk only through facades

Derive the order from the foreign-key graph: a module sits above every module its tables point at. A module imports only modules **below** it, and only through their facade (`<module>/__init__.py`), plus their `models` (D4). The facade exports exactly what callers use.

- **Why:** without an order, modules import each other in cycles, cycles get dodged with imports inside functions, and services reach into other modules' repositories. A fixed order makes every dependency question answerable by a list.
- **Rejected:** "any module may call any facade" (cycles return); import-inside-function to break a cycle (a cycle is a design error to fix, not to hide).
- **Enforced by:** module-order and facade-only tests, with an exact module-list test so a new module cannot slip in unordered.

## D3 — One injected unit of work per use case; only the outermost use case commits (L)

Every service and repository receives the same unit of work, a thin wrapper over one database session. Nothing below the entry point opens a session. Only the outermost use case calls `commit()`, and it commits **before** any external I/O (identity provider, PDF rendering, email, HTTP calls). HTTP builds the unit of work per request; cron jobs, schedulers and scripts build the same object with a context manager; tests bind it to an outer transaction that is rolled back.

- **Why:** services that open their own sessions split one request across several transactions. One part commits while another fails, and the request holds several pool connections. Committing after external I/O sends emails for rows that then roll back.
- **Rejected:** a request-scoped session committed by the framework's dependency teardown (hidden commit point, HTTP-only, and in FastAPI's default scope it commits after the response is sent); a use case that opens its own unit of work without injection (regresses as soon as one collaborator opens a session again); an ambient context-variable session (a hidden global that background tasks outlive).
- **Enforced by:** a test that fails on the session-factory call anywhere under the modules package, with an explicit allow-list for sanctioned exceptions (for example after-response notification jobs).

## D4 — Read any model, write only your own tables (L for the SQL rule)

ORM models are a shared layer beneath the module order: any repository may select or join any model. Inserts, updates and deletes touch only the module's own tables; a write to another module's table goes through that module's facade. A read view spanning modules lives in the module that serves it. Raw SQL lives only in repositories.

- **Why:** read views (a student profile with payments and attendance) legitimately span modules. Forbidding cross-module reads forces a separate read layer or a router calling many facades per page. Writes are where ownership matters.
- **Rejected:** facade calls for every cross-module read; a separate read-model layer.
- **Consequence:** an existing calculation (a balance, a rate) is reused through its owner's facade when the owner is lower. When the owner is higher, the view moves up to the owner instead of duplicating the calculation in SQL.
- **Enforced by:** the module-order test exempts `models` imports; write ownership and raw-SQL placement are review checks.

## D5 — Identity is the bottom module

The module owning users, roles, login and the audit log sits at the bottom: almost every table has an audit foreign key (`created_by`) pointing at users. Staff or member records live in a module above it. "Give this person a login" is a use case in the upper module calling one identity facade function (`provision_login`), the only place logins are created.

- **Why:** when identity and staff records import each other, login creation multiplies (three code paths in the source system) and the order cannot be drawn.
- **Rejected:** identity above staff (audit FKs then point upward); merging identity and staff records into one module (mixes HR data with security code).

## D6 — A write workflow spanning modules lives in the highest module involved

A single-transaction workflow that writes to several modules belongs to the highest module it touches, which is usually the one owning the record the workflow produces. It calls lower modules through their facades and runs in one unit of work. Endpoints move with it, keeping their paths.

- **Why:** a lower module calling up into a higher one breaks the order (D2) for the most important code path, the one that must be atomic.
- **Rejected:** a port per upward call (an interface for a core step of one transaction; ports are for after-commit side effects, D7); a top-level `workflows/` layer (a second place to look that becomes a catch-all).

## D7 — Modules notify through their own notifier ports, called after commit

A module that emits notifications defines a small port (2–5 methods, named for its events) in its own package. The notifications module, high in the order, implements every port as an adapter. A use case calls its notifier after `commit()`. Adapters are wired in the composition root (the app factory), never by the emitting module, so lower modules never import notifications. Services take no framework objects such as background-task queues; the adapter decides how to dispatch (queued during HTTP, inline in cron).

- **Why:** modules importing a central notification service create upward imports, and passing the framework's background-task object into services ties them to HTTP; cron paths passed `None` and silently skipped notifications.
- **Enforced by:** module-order test (no lower module imports notifications); each port has a real adapter and a test fake (D8).

## D8 — An interface exists only where two adapters satisfy it

Keep a Protocol/ABC only when at least two implementations exist; a test fake counts. Callers and type hints otherwise use the concrete class. Introduce the interface when the second adapter appears.

- **Why:** one-implementation interfaces doubled the files to read without letting anything vary; most per-slice interfaces in the source system had zero references.
- **Rejected:** an interface for every service and repository "as the contract".

## D9 — Services may call sibling services through the shared unit of work

Within one module, a use-case service may call another service of the same module, passing the same unit of work, so the call stays in one transaction. Services never construct their own dependencies or sessions; the module's `api/` factories (or the entry point) build them.

- **Why:** forbidding sibling calls pushes business rules down into repositories or helpers. Default-constructed dependencies (`self.x = x or XService()`) hide a second session and make the transaction boundary invisible.
- **Rejected:** a separate use-case layer above services (a sixth layer); "services never call services".

## D10 — Validation splits by kind (L)

Format and shape checks (phone format, positive amounts, non-empty strings) live on the schemas as validators. Rules that need the database or business state (uniqueness, allowed transitions) live in services. There is no `validators/` layer, and repositories validate nothing.

## D11 — Repositories are classes over the session, with zero business rules (L for "zero business rules")

A repository is a class constructed with the unit of work's session. It runs queries and returns models or DTOs; it holds no business rules, no validation, no orchestration.

- **Why:** a class built from the injected session makes the transaction boundary explicit (D3); module-level query functions tend to grab a session of their own.

## D12 — Typed contracts (L)

Services and repositories return named DTOs or ORM models, never a bare `dict`, `list[dict]` or `tuple`. DTO names: input `{Operation}{Entity}Input`, result `{Entity}{Operation}Result`, read model `{Entity}{Qualifier}DTO`. HTTP response schemas live in `api/` and wrap or reuse service DTOs; services never import them (D1).

## D13 — Delete dead code before moving anything (L)

Before a move, grep for callers of every function and method in scope. Code with no callers is deleted, never migrated. No deprecated shims, no backward-compatibility aliases, no commented-out code, no subset method kept beside the superset that callers actually use.

- **Why:** dead code moved into a new structure looks deliberate, and someone calls it.
