# dropbox_upload.py
import logging
import os
from pathlib import Path

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

from config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN

logger = logging.getLogger(__name__)

def _get_client():
    if not (DROPBOX_APP_KEY and DROPBOX_APP_SECRET and DROPBOX_REFRESH_TOKEN):
        raise ValueError("Dropbox credentials were not found in .env")
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
    )

def upload_file(local_path, dbx):
    """Uploads local_path to the app folder's root, overwriting any existing file of the same name."""
    filename = os.path.basename(local_path)
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), f"/{filename}", mode=WriteMode.overwrite)
    logger.info("Uploaded %s to Dropbox", filename)

def upload_files(paths):
    dbx = _get_client()
    for path in paths:
        upload_file(path, dbx)

def download_file(local_path, dbx):
    """Downloads a same-named file from the app folder's root to local_path.
    Does nothing if it doesn't exist on Dropbox yet (e.g. the very first run)."""
    local_path = Path(local_path)
    filename = local_path.name
    try:
        dbx.files_download_to_file(str(local_path), f"/{filename}")
        logger.info("Restored %s from Dropbox", filename)
    except ApiError as exc:
        if exc.error.is_path() and exc.error.get_path().is_not_found():
            logger.info("%s not found on Dropbox yet (first run)", filename)
        else:
            raise

def download_files(paths):
    dbx = _get_client()
    for path in paths:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        download_file(path, dbx)
