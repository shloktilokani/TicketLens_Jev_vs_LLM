from typing import Annotated

from fastapi import Depends, Request
from pymongo.database import Database


def get_db(request: Request) -> Database:
    return request.app.state.db


Db = Annotated[Database, Depends(get_db)]
