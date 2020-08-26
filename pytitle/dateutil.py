import pytz
from datetime import datetime, timezone

def get_now_iso8601_datetime_cst():
    utc_dt = datetime.now(timezone.utc)
    CST = pytz.timezone('US/Central')
    return utc_dt.astimezone(CST).isoformat()