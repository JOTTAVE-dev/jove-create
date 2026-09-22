from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def get_app_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().app_timezone)


def now_local() -> datetime:
    return datetime.now(tz=get_app_timezone())
