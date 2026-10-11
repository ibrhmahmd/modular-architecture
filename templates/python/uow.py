"""Unit of Work: one transaction boundary per use case (decision D3).

A use case receives exactly one UnitOfWork; only the outermost use case calls
commit(), and it does so before any external I/O. Edit the get_engine import.
"""
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session

from app.db.connection import get_engine  # EDIT: the project's engine factory


class UnitOfWork:
    """Wraps one Session. Services and repositories share the injected instance."""

    def __init__(self, session: Session):
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def flush(self) -> None:
        self._session.flush()


@contextmanager
def unit_of_work() -> Iterator[UnitOfWork]:
    """UnitOfWork for any entry point (HTTP dependency, cron, scheduler, script).

    Never auto-commits: whatever the use case did not commit is rolled back on
    exit, and an exception is re-raised after rollback. The session always closes.
    """
    with Session(get_engine(), expire_on_commit=False) as session:
        uow = UnitOfWork(session)
        try:
            yield uow
        finally:
            session.rollback()
