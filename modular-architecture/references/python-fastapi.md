# Stack notes: Python, FastAPI, SQLAlchemy / SQLModel

Concrete forms of the decisions for this stack. Paths assume the app package is `app/` and modules live in `app/modules/`; adjust to the project.

## Layout

```text
app/
  api/                 shared HTTP only: create_app(), router registry, middleware,
                       exception handlers, auth guards, response envelope, get_uow
  db/uow.py            UnitOfWork + unit_of_work()
  shared/              platform helpers usable by every module
  modules/<name>/
    api/  routers.py, schemas/, deps.py (service factories, notifier providers)
    services/  repositories/  schemas/  models/
    __init__.py        facade with an explicit __all__
```

## Unit of work (D3)

Copy [templates/python/uow.py](../templates/python/uow.py) to `app/db/uow.py`. The HTTP dependency:

```python
def get_uow() -> Iterator[UnitOfWork]:
    with unit_of_work() as uow:
        yield uow

# scope="function" ends the dependency before the response is sent, so a
# failed commit becomes an error response instead of a 200 already sent.
UoW = Annotated[UnitOfWork, Depends(get_uow, scope="function")]
```

`Depends(..., scope=...)` needs a FastAPI release that supports dependency scopes; check the installed version. On an older one, commit inside the route (the use case's top) so the commit still happens before the response.

Service factories live in the module's `api/deps.py` and only build objects:

```python
def get_enrollment_service(uow: UoW) -> EnrollmentService:
    return EnrollmentService(uow)
```

The use case commits, then notifies:

```python
def enroll(self, data: EnrollStudentInput) -> EnrollmentResult:
    enrollment = self._repo.create(...)
    self._uow.commit()                      # before any external I/O
    self._notifier.enrollment_created(...)  # D7: after commit
    return EnrollmentResult.model_validate(enrollment)
```

Cron, schedulers and scripts: `with unit_of_work() as uow: SomeService(uow).run(); ...`.

## Repositories (D11)

```python
class EnrollmentRepository:
    def __init__(self, session: Session):
        self._session = session

    def get(self, enrollment_id: int) -> Enrollment | None:
        return self._session.get(Enrollment, enrollment_id)
```

Built inside the service from `uow.session`. Raw `text()` SQL only here (D4).

## Notifier ports (D7)

```python
# app/modules/enrollments/notifier.py — the port, 2–5 methods
class EnrollmentNotifier(Protocol):
    def enrollment_created(self, enrollment_id: int, student_id: int) -> None: ...

# app/modules/enrollments/api/deps.py — provider the composition root replaces
def get_enrollment_notifier() -> EnrollmentNotifier:
    raise NotImplementedError("wired in create_app()")

# app/api/main.py — create_app(), the only place adapters are wired
app.dependency_overrides[enrollments_deps.get_enrollment_notifier] = notifications_adapters.get_enrollment_notifier
```

The HTTP adapter receives FastAPI's `BackgroundTasks` and queues; the cron adapter sends inline. A notifier failure is logged and never fails the use case. Background jobs that run after the response open their own session inside the adapter: that path goes on the session-factory allow-list.

## Test fixtures

A unit of work bound to an outer transaction, so even committed work leaves no rows:

```python
@pytest.fixture
def uow():
    connection = get_engine().connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield UnitOfWork(session)
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def client_with_uow(app, uow):
    app.dependency_overrides[get_uow] = lambda: uow
    try:
        yield TestClient(app)   # not as a context manager: the lifespan (schedulers) stays off
    finally:
        app.dependency_overrides.pop(get_uow, None)
```

Legacy code that opens its own sessions cannot see rows inside this transaction; characterization tests for legacy endpoints seed committed, uniquely tagged rows and delete them afterwards.

## Enforcement tests

Copy [templates/python/architecture/](../templates/python/architecture/) to `tests/architecture/`, then:

1. In `conftest.py`, set `ROOT_PACKAGE`, `MODULES_PACKAGE`, `MODULES` (top to bottom), `SESSION_FACTORY` and its allow-list.
2. In `test_openapi_snapshot.py`, point the import at the app factory and create the snapshot with `UPDATE_OPENAPI_SNAPSHOT=1`.
3. `pip install grimp` (dev dependency). Run `pytest tests/architecture -q` and read the summary table.

`ENFORCED_MODULES` starts empty in a legacy codebase and grows by one module per finished migration.

## Pitfalls

- **Route order.** FastAPI matches in registration order: `/groups/{group_id}` registered before `/groups/enriched` swallows it. Moving routers between files can reorder registration; the snapshot does not catch it, characterization tests of the literal route do.
- **`exec` versus `execute`.** SQLModel's `session.exec(select(func.count()))` returns scalars, so `.one()` gives an `int`, and the result has no `.scalar()`. SQLAlchemy's `session.execute(...)` returns rows: use `.scalar_one()`. Multi-column selects return row tuples either way.
- **`from_attributes`.** A DTO validated from an ORM object needs `model_config = ConfigDict(from_attributes=True)`.
- **Imports inside functions** that exist to dodge a circular import still count: grimp reads every import statement, nested ones included. Remove them when the module migrates and fix the cycle.
- **Swallowed rollbacks.** A legacy request-scoped session that commits in dependency teardown still commits after a caught exception: re-raise after rollback until the module is on the unit of work.
