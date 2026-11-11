"""Empty the UI-test database so every test-stack start begins clean.

Usage: backend/.venv/bin/python e2e/scripts/reset_db.py ticketlens_e2e
Refuses any database whose name does not end in _e2e, so it can never drop real data.
"""

import sys
from pathlib import Path

from pymongo import MongoClient

# The backend's settings module is the one place config is read, so reuse it.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.core.settings import get_settings

name = sys.argv[1] if len(sys.argv) == 2 else ""
if not name.endswith("_e2e"):
    sys.exit(f"Refusing to reset {name!r}: only databases ending in _e2e can be reset.")

with MongoClient(get_settings().mongodb_uri, serverSelectionTimeoutMS=3000) as client:
    client.drop_database(name)
print(f"Reset database {name}")
