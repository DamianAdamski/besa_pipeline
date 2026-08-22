# dropbox_upload.py
import logging
import os

import dropbox
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
