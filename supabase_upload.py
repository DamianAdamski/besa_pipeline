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


def _upload_clients(client, client_dim):
    if client_dim is None or client_dim.empty:
        return 0
    rows = [
        {
            "client_id": _clean_value(row["client_id"]),
            "client_name": _clean_value(row.get("client_name")),
            "sales_channel": _clean_value(row.get("sales_channel")),
            "client_email_address": _clean_value(row.get("client_email_address")),
            "client_phone_number": _clean_value(row.get("client_phone_number")),
            "client_street_name": _clean_value(row.get("client_street_name")),
            "client_post_code": _clean_value(row.get("client_post_code")),
            "client_outward_code": _clean_value(row.get("client_outward_code")),
            "client_inward_code": _clean_value(row.get("client_inward_code")),
            "client_city": _clean_value(row.get("client_city")),
        }
        for _, row in client_dim.iterrows()
    ]
    client.table("besa_clients").upsert(rows, on_conflict="client_id").execute()
    return len(rows)


def _upload_project_dim(client, project_dim):
    if project_dim is None or project_dim.empty:
        return 0
    rows = [
        {
            "project_id": _clean_value(row["project_id"]),
            "project_name": _clean_value(row.get("project_name")),
            "project_status": _clean_value(row.get("project_status")),
            "project_start_date": _clean_date(_clean_value(row.get("project_start_date"))),
            "project_end_date": _clean_date(_clean_value(row.get("project_end_date"))),
            "client_id": _clean_value(row.get("client_id")),
        }
        for _, row in project_dim.iterrows()
    ]
    client.table("besa_projects").upsert(rows, on_conflict="project_id").execute()
    return len(rows)


def _upload_project_facts(client, project_fact):
    if project_fact is None or project_fact.empty:
        return 0
    rows = [
        {
            "project_id": _clean_value(row["project_id"]),
            "project_value": _clean_value(row.get("project_value")),
            "dardan_days_worked": _clean_value(row.get("dardan_days_worked")),
            "musa_days_worked": _clean_value(row.get("musa_days_worked")),
            "dori_days_worked": _clean_value(row.get("dori_days_worked")),
            "remzi_days_worked": _clean_value(row.get("remzi_days_worked")),
            "total_material_cost": _clean_value(row.get("total_material_cost")),
        }
        for _, row in project_fact.iterrows()
    ]
    client.table("besa_project_facts").upsert(rows, on_conflict="project_id").execute()
    return len(rows)


def _upload_expenses(client, material_fact):
    # No stable natural key per line item (two identical expense rows for the
    # same project are indistinguishable), and the pipeline always has the full
    # current snapshot in materials_df (not just this run's changes) - so a full
    # replace is simpler and safer than trying to diff/upsert individual rows.
    client.table("besa_expenses").delete().gt("id", 0).execute()

    if material_fact is None or material_fact.empty:
        return 0
    rows = [
        {
            "project_id": _clean_value(row.get("project_id")),
            "expense_name": _clean_value(row.get("expense_name")),
            "expense_cost": _clean_value(row.get("expense_cost")),
            "quantity": _clean_value(row.get("quantity")),
        }
        for _, row in material_fact.iterrows()
    ]
    client.table("besa_expenses").insert(rows).execute()
    return len(rows)


def _upload_subtasks(client, services_df):
    # Unlike expenses, ClickUp subtasks have a real stable id (subtask_id),
    # so this is a normal upsert rather than a delete-all-then-insert.
    if services_df is None or services_df.empty:
        return 0
    rows = [
        {
            "subtask_id": _clean_value(row["subtask_id"]),
            "project_id": _clean_value(row.get("project_id")),
            "subtask_name": _clean_value(row.get("subtask_name")),
            "order_index": _clean_value(row.get("order_index")),
            "service_price": _clean_value(row.get("service_price")),
            "service_description": _clean_value(row.get("service_description")),
        }
        for _, row in services_df.iterrows()
    ]
    client.table("besa_project_subtasks").upsert(rows, on_conflict="subtask_id").execute()
    return len(rows)


def _drop_orphans(df, valid_project_ids, table_name):
    """material_fact/services_df can reference a project_id that never appears
    as its own row in project_dim (e.g. a subtask whose parent task was deleted
    or archived in ClickUp) - besa_expenses/besa_project_subtasks both have a
    foreign key to besa_projects, so uploading such a row would violate it and
    abort the whole sync. Dropping them here (with a visible warning) is safer
    than either crashing the run or silently relaxing the foreign key."""
    if df is None or df.empty:
        return df
    known = df["project_id"].isin(valid_project_ids)
    if (~known).any():
        orphans = df.loc[~known, "project_id"].unique()
        logger.warning(
            "Dropping %d %s row(s) referencing %d unknown project_id(s) (parent likely deleted/archived in ClickUp): %s",
            (~known).sum(), table_name, len(orphans), list(orphans),
        )
    return df[known]


def sync_all(client_dim, project_dim, project_fact, material_fact, services_df):
    """Mirrors all of besa_pipeline's output tables into Supabase, in FK-safe
    order: clients before projects (projects.client_id references besa_clients),
    then projects before facts/expenses/subtasks (all three reference besa_projects)."""
    client = _get_client()

    valid_project_ids = set(project_dim["project_id"]) if project_dim is not None and not project_dim.empty else set()
    material_fact = _drop_orphans(material_fact, valid_project_ids, "besa_expenses")
    services_df = _drop_orphans(services_df, valid_project_ids, "besa_project_subtasks")

    n_clients = _upload_clients(client, client_dim)
    n_projects = _upload_project_dim(client, project_dim)
    n_facts = _upload_project_facts(client, project_fact)
    n_expenses = _upload_expenses(client, material_fact)
    n_subtasks = _upload_subtasks(client, services_df)

    logger.info(
        "Synced to Supabase: %d clients, %d projects, %d project facts, %d expenses, %d subtasks",
        n_clients, n_projects, n_facts, n_expenses, n_subtasks,
    )
