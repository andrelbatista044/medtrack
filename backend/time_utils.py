from datetime import date, datetime
from zoneinfo import ZoneInfo

from .database import settings


def local_now() -> datetime:
    """Return application-local time as a naive datetime for DB compatibility."""
    return datetime.now(ZoneInfo(settings.app_timezone)).replace(tzinfo=None)


def local_today() -> date:
    return local_now().date()
