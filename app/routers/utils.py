from datetime import date, datetime
from typing import Any


def json_serial(obj: Any) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)
