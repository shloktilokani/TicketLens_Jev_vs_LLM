"""TicketLens API entry point.

Phase 1 scaffold: starts with no provider keys and no database. Routes and settings arrive in
later phases (see implementation.md).
"""

from fastapi import FastAPI

app = FastAPI(title="TicketLens API", version="0.1.0")
