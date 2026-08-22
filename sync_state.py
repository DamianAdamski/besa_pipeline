# sync_state.py
import json
import logging

from config import LAST_SYNC_FILE

logger = logging.getLogger(__name__)

def load_last_sync_ts():
    """Returns the ms-epoch timestamp of the last successful run, or None if there isn't one."""
    if not LAST_SYNC_FILE.exists():
        return None
    try:
        with open(LAST_SYNC_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_sync_ts")
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read last sync state (%s); falling back to a full fetch", exc)
        return None

def save_last_sync_ts(ts):
    LAST_SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_SYNC_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_sync_ts": ts}, f)
