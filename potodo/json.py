from datetime import date
from typing import Optional


def json_dateconv(o: object) -> Optional[str]:
    if isinstance(o, date):
        return str(o)
    return None
