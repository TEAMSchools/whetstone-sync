import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

WHETSTONE_DISTRICT_ID = os.getenv("WHETSTONE_DISTRICT_ID")
LOCAL_TIMEZONE = os.getenv("LOCAL_TIMEZONE")

today = datetime.now().replace(
    hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo(LOCAL_TIMEZONE)
)
last_modified = today - timedelta(days=280)
last_modified_ts = last_modified.timestamp()

USER_ENDPOINTS = [
    {"path": "users"},
    {"path": "users", "params": {"archived": True}},
]

ENDPOINTS = [
    {"path": "assignments", "params": {"lastModified": last_modified_ts}},
    {
        "path": "assignments",
        "params": {"archived": True, "lastModified": last_modified_ts},
    },
    {"path": "roles", "params": {"district": WHETSTONE_DISTRICT_ID}},
    {"path": "informals"},
    {"path": "measurements"},
    {"path": "meetings"},
    {"path": "rubrics"},
    {"path": "schools"},
    {"path": "videos"},
    {"path": "lessonplans/forms"},
    {"path": "lessonplans/groups"},
    {"path": "lessonplans/reviews"},
    {"path": "roles", "params": {"district": WHETSTONE_DISTRICT_ID, "archived": True}},
    {"path": "informals", "params": {"archived": True}},
    {"path": "measurements", "params": {"archived": True}},
    {"path": "meetings", "params": {"archived": True}},
    {"path": "rubrics", "params": {"archived": True}},
    {"path": "schools", "params": {"archived": True}},
    {"path": "videos", "params": {"archived": True}},
    {"path": "lessonplans/forms", "params": {"archived": True}},
    {"path": "lessonplans/groups", "params": {"archived": True}},
    {"path": "lessonplans/reviews", "params": {"archived": True}},
    {"path": "observations", "params": {"lastModified": last_modified_ts}},
    {
        "path": "observations",
        "params": {"archived": True, "lastModified": last_modified_ts},
    },
]
