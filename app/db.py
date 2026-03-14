from flask import g
from app.models import SessionLocal


def get_db():
    """Return the per-request SQLAlchemy session, creating it on first access."""
    if "db" not in g:
        g.db = SessionLocal()
    return g.db


def teardown_db(exc):
    """Close the per-request SQLAlchemy session at the end of the app context."""
    db = g.pop("db", None)
    if db is not None:
        db.close()
