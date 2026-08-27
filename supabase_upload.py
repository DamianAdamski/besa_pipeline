# supabase_upload.py
import logging
import math

from supabase import create_client

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)


def _get_client():
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
        raise ValueError("Supabase credentials were not found in .env")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _clean_date(value):
    """project_dim stores 'N/A' for a missing date (see transform.split_clean_tables);
    Supabase's date column needs either a real date string or None."""
    if not value or value == "N/A":
        return None
    return value


def _clean_value(value):
    """pandas represents any missing value (including in string columns, despite
    upstream fillna) as float NaN, which isn't valid JSON and would break the
    upsert request - so every field gets funneled through this at the pandas/JSON
    boundary, not just the ones known to need it today."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def upload_projects(project_dim, project_fact, client_dim):
    """Upserts one row per project into besa_projects, so the Mapogos Pricing app
    can offer real ClickUp projects to price against and later compare predicted
    price to actual accepted price (project_fact's project_value)."""
    if project_dim is None or project_dim.empty:
        logger.info("No projects to sync to Supabase")
        return

    value_by_id = (
        dict(zip(project_fact["project_id"], project_fact["project_value"]))
        if project_fact is not None and not project_fact.empty
        else {}
    )
    client_name_by_id = (
        dict(zip(client_dim["client_id"], client_dim["client_name"]))
        if client_dim is not None and not client_dim.empty
        else {}
    )

    rows = [
        {
            "project_id": _clean_value(row["project_id"]),
            "project_name": _clean_value(row.get("project_name")),
            "client_name": _clean_value(client_name_by_id.get(row.get("client_id"))),
            "project_status": _clean_value(row.get("project_status")),
            "project_start_date": _clean_date(_clean_value(row.get("project_start_date"))),
            "project_end_date": _clean_date(_clean_value(row.get("project_end_date"))),
            "project_value": _clean_value(value_by_id.get(row["project_id"])),
        }
        for _, row in project_dim.iterrows()
    ]

    client = _get_client()
    client.table("besa_projects").upsert(rows, on_conflict="project_id").execute()
    logger.info("Synced %d projects to Supabase", len(rows))
