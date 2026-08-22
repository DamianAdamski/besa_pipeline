# main.py
import datetime
import logging
import sys
import time

import pandas as pd

from config import BESA_CLIENTS_LIST_ID, RAW_DATA_FILE, CLEAN_DATA_DIR, LOG_FILE
from extract import get_all_tasks, get_task_details, get_subtasks
from transform import (
    build_projects_table, build_materials_table, build_services_table, build_labor_table,
    split_clean_tables, clean_project_addresses,
    merge_projects_table, merge_materials_table, merge_services_table,
)
from export import export_to_excel, export_clean_tables_to_excel, export_clean_tables_to_csv
from sync_state import load_last_sync_ts, save_last_sync_ts
from dropbox_upload import upload_files

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),               # prints to the terminal, as before
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # appends to a persistent log file
    ],
)
logger = logging.getLogger(__name__)


def load_previous_raw_tables():
    """Reads back the last full export to merge freshly-fetched rows into. Returns
    (None, None, None) on a first run, or if the file can't be read."""
    if not RAW_DATA_FILE.exists():
        return None, None, None
    try:
        sheets = pd.read_excel(RAW_DATA_FILE, sheet_name=["Projects", "Materials", "Services"])
        return sheets["Projects"], sheets["Materials"], sheets["Services"]
    except (ValueError, OSError) as exc:
        logger.warning("Could not read previous raw data (%s); doing a full fetch", exc)
        return None, None, None


def run_pipeline():
    logger.info("Starting BESA pipeline run")

    last_sync_ts = load_last_sync_ts()
    run_started_at = int(time.time() * 1000)

    prev_projects_df, prev_materials_df, prev_services_df = load_previous_raw_tables()
    has_baseline = prev_projects_df is not None

    if last_sync_ts and not has_baseline:
        logger.warning(
            "Sync state found but no previous raw data to merge into (%s missing or unreadable); "
            "falling back to a full fetch", RAW_DATA_FILE
        )
        last_sync_ts = None

    if last_sync_ts:
        readable_ts = datetime.datetime.fromtimestamp(last_sync_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Incremental run: fetching tasks updated since %s", readable_ts)
    else:
        logger.info("No previous sync state found; doing a full fetch")

    all_tasks = get_all_tasks(BESA_CLIENTS_LIST_ID, date_updated_gt=last_sync_ts)
    logger.info("Fetched %d changed tasks", len(all_tasks))

    changed_project_ids = {t["id"] for t in all_tasks}
    detailed_tasks = get_task_details([t["id"] for t in all_tasks])
    subtasks = get_subtasks(BESA_CLIENTS_LIST_ID, date_updated_gt=last_sync_ts)
    logger.info("Fetched details for %d tasks and %d changed subtasks", len(detailed_tasks), len(subtasks))

    new_raw_project_df = build_projects_table(detailed_tasks)
    new_materials_df = build_materials_table(detailed_tasks)

    raw_project_df = merge_projects_table(prev_projects_df, new_raw_project_df)
    materials_df = merge_materials_table(prev_materials_df, new_materials_df, changed_project_ids)

    # Fallback project names for subtasks whose parent project wasn't fetched this run
    if "project_id" in raw_project_df.columns:
        project_names = dict(zip(raw_project_df["project_id"], raw_project_df["project_name"]))
    else:
        project_names = {}
    new_services_df = build_services_table(detailed_tasks, subtasks, fallback_names=project_names)
    services_df = merge_services_table(prev_services_df, new_services_df)

    cln_project_df = clean_project_addresses(raw_project_df)
    # labor_df = build_labor_table(ongoing_tasks, existing_df=None)

    export_to_excel(cln_project_df, materials_df, services_df)

    client_dim, project_dim, project_fact, material_fact, labor_fact = split_clean_tables(
        cln_project_df, materials_df)

    export_clean_tables_to_excel(client_dim, project_dim, project_fact, material_fact)
    export_clean_tables_to_csv(client_dim, project_dim, project_fact, material_fact)

    logger.info("Uploading results to Dropbox")
    upload_files([
        RAW_DATA_FILE,
        CLEAN_DATA_DIR / "besaconstruction_clean_data.xlsx",
        CLEAN_DATA_DIR / "ClientDim.csv",
        CLEAN_DATA_DIR / "ProjectDim.csv",
        CLEAN_DATA_DIR / "ProjectFact.csv",
        CLEAN_DATA_DIR / "ExpenseFact.csv",
    ])

    save_last_sync_ts(run_started_at)
    logger.info("Pipeline run completed successfully")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception:
        logger.exception("Pipeline run failed")
        sys.exit(1)
