"""Create the TicketLens MongoDB indexes. Safe to run more than once.

Run from backend/:  .venv/bin/python -m scripts.init_db
"""

import sys

from pymongo.errors import PyMongoError

from app.core.settings import get_settings
from app.repositories.database import DB_UNAVAILABLE_MESSAGE, connect, ensure_indexes


def main() -> int:
    settings = get_settings()
    client = connect(settings)
    try:
        ensure_indexes(client[settings.mongodb_database])
    except PyMongoError:
        print(DB_UNAVAILABLE_MESSAGE, file=sys.stderr)
        return 1
    finally:
        client.close()
    print(f"Indexes are in place in database '{settings.mongodb_database}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
