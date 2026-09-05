# transform.py
import re
import pandas as pd
import datetime
from extract import get_task_texts, labor_text_to_table

# ----------------------
# Helpers
# ----------------------
def get_custom_field_value(custom_fields, field_name):
    for field in custom_fields:
        if field.get("name") == field_name:
            return field.get("value")
    return None

def get_custom_field_option_name(custom_fields, field_name):
    for field in custom_fields:
        if field.get("name") == field_name and "value" in field:
            value = field["value"]
            for option in field.get("type_config", {}).get("options", []):
                if option.get("orderindex") == value:
                    return option["name"]
    return None

def safe_timestamp_to_date(ts):
    if ts:
        return datetime.datetime.fromtimestamp(int(ts) / 1000).strftime('%Y-%m-%d')
    return None

# ----------------------
# Projects Table
# ----------------------
def build_projects_table(tasks):
    data = []
    for task in tasks:
        cf = task.get("custom_fields", [])
        row = {
            "project_id": task.get("id"),
            "client_name": get_custom_field_value(cf, "Client Name"),
            "sales_channel": get_custom_field_option_name(cf, "How did you hear about us?"),
            "project_name": task.get("name"),
            "client_address": get_custom_field_value(cf, "Project Address"),
            "client_email_address": get_custom_field_value(cf, "Email Address"),

            "client_phone_number": get_custom_field_value(cf, "Phone Number"),
            "project_status": task.get("status", {}).get("status"),
            "project_start_date": safe_timestamp_to_date(task.get("start_date")),
            "project_end_date": safe_timestamp_to_date(task.get("due_date")),
            "project_value": get_custom_field_value(cf, "Total Price (excl. VAT%)"),
            "dardan_days_worked": get_custom_field_value(cf, "01 Dardan (days worked)"),
            "musa_days_worked": get_custom_field_value(cf, "02 Musa (days worked)"),
            "dori_days_worked": get_custom_field_value(cf, "03 Dori (days worked)"),
            "remzi_days_worked": get_custom_field_value(cf, "04 Remzi (days worked)"),
        }
        data.append(row)

    df = pd.DataFrame(data)
    return df

# ----------------------
# Cleaning Projects Table
# ----------------------

def clean_project_addresses(df):
    # Flexible UK postcode regex
    postcode_regex = r'([A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2})'
    
    def extract_parts(address):
        if not isinstance(address, str):
            return None, None, None, None, None, None

        # Normalize spaces & uppercase
        addr = re.sub(r'\s+', ' ', address.strip()).upper()

        # Find postcode
        m = re.search(postcode_regex, addr, re.IGNORECASE)
        if not m:
            return addr, None, None, None, None, addr
        
        postcode = m.group(1).strip()
        
        # Split outward & inward
        m2 = re.match(r'([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})', postcode)
        outward = m2.group(1).upper() if m2 else None
        inward = m2.group(2).upper() if m2 else None
        
        # Break address into parts
        before_postcode = addr[:m.start()].strip(" ,")
        after_postcode = addr[m.end():].strip(" ,")

        city = None
        street = before_postcode
        
        # Case 1: city is before postcode (look for last comma section)
        if ',' in before_postcode:
            tokens = [t.strip() for t in before_postcode.split(',')]
            street = ', '.join(tokens[:-1])
            city = tokens[-1]
        
        # Case 2: city is after postcode
        if after_postcode:
            city = after_postcode
        
        return street, postcode, outward, inward, city, addr
    
    
    parts = df['client_address'].apply(lambda x: pd.Series(extract_parts(x)))
    parts.columns = ['client_street_name', 
                     'client_post_code', 
                     'client_outward_code', 
                     'client_inward_code', 
                     'client_city',
                     'client_address']
    
    return pd.concat([df.drop(columns=[
        "client_street_name", 
        "client_post_code", 
        "client_outward_code", 
        "client_inward_code", 
        "client_city", 
        "client_address"
    ], errors="ignore"), parts], axis=1)

# ----------------------
# Materials Table
# ----------------------
def build_materials_table(tasks):
    material_data = []
    for task in tasks:
        project_id = task.get("id")
        project_name = task.get("name")
        for checklist in task.get("checklists", []):
            for item in checklist.get("items", []):
                raw_name = item.get("name", "").strip()
                match_full = re.match(r"^(.*?)[\s\-]+(\d+(?:\.\d+)?)[\s\-]+(\d+)$", raw_name)
                match_cost_only = re.match(r"^(.*?)[\s\-]+(\d+(?:\.\d+)?)$", raw_name)

                if match_full:
                    expense_name, expense_cost, quantity = match_full.group(1).strip(), float(match_full.group(2)), int(match_full.group(3))
                elif match_cost_only:
                    expense_name, expense_cost, quantity = match_cost_only.group(1).strip(), float(match_cost_only.group(2)), 1
                else:
                    expense_name, expense_cost, quantity = raw_name, None, None

                material_data.append({
                    "project_id": project_id,
                    "project_name": project_name,
                    "expense_name": expense_name,
                    "expense_cost": expense_cost,
                    "quantity": quantity
                })

    return pd.DataFrame(material_data)

# ----------------------
# Services Table
# ----------------------
def build_services_table(tasks, subtasks, fallback_names=None):
    """
    fallback_names: optional {project_id: project_name} map used when a subtask's
    parent project wasn't among `tasks` (e.g. on an incremental run where only the
    subtask changed) — without it, the project name would resolve to None.
    """
    task_id_to_name = {task["id"]: task["name"] for task in tasks}
    fallback_names = fallback_names or {}
    subtasks_data = []

    for subtask in subtasks:
            parent_id = subtask.get("parent")
            if not parent_id:
                continue        # skip subtasks without parent

            cf = subtask.get("custom_fields",[])
            project_name = task_id_to_name.get(parent_id) or fallback_names.get(parent_id)
            
            subtasks_data.append({
                    "project_id": parent_id,
                    "project_name": project_name,
                    "subtask_id": subtask["id"],
                    "subtask_name": subtask['name'],
                    # Kept as the original string (not float()) so Postgres's numeric
                    # column parses it with full precision - ClickUp's orderindex has
                    # far more significant digits than a 64-bit float can hold, and it's
                    # what actually reflects a task's position among siblings (including
                    # manual drag-to-reorder), unlike date_created.
                    "order_index": subtask.get("orderindex"),
                    "service_price": get_custom_field_value(cf,'Total Price (excl. VAT%)'),
                    "service_description": get_custom_field_value(cf,'Service Description')
            })
     
    return pd.DataFrame(subtasks_data)


# ----------------------
# Labor Table
# ----------------------
def build_labor_table(tasks, existing_df=None):
    """
    Loops through all tasks and combines their labor logs into one DataFrame.
    Keeps existing labor data (if provided) and appends new tasks.
    
    Parameters:
        tasks (list): List of task dictionaries
        existing_df (pd.DataFrame, optional): Existing labor table to keep
    
    Returns:
        pd.DataFrame: Updated labor table sorted by Date
    """
    task_texts = get_task_texts(tasks) 
    all_labor = []

    # Keep existing data if provided
    if existing_df is not None:
        all_labor.append(existing_df)
        existing_task_ids = set(existing_df['project_id'].unique())
    else:
        existing_task_ids = set()

    for task_id, text in task_texts.items():
        # Only process tasks that are not already in existing_df
        if task_id not in existing_task_ids and text.strip():  
            df = labor_text_to_table(text, task_id) 
            if not df.empty: 
                all_labor.append(df)

    if all_labor: 
        labor_df = pd.concat(all_labor, ignore_index=True)

        # Convert 'Date' to datetime and sort chronologically
        labor_df['Date'] = pd.to_datetime(labor_df['Date'], format='%d.%m.%y')
        labor_df = labor_df.sort_values('Date').reset_index(drop=True)

        return labor_df

    return existing_df if existing_df is not None else pd.DataFrame()

# Merging raw tables (incremental sync)

# These upsert rows (for tasks changed since the last run) into the
# previous full snapshot, so the pipeline can fetch only what changed while still
# exporting a complete dataset. They do not detect tasks deleted in ClickUp.
def merge_projects_table(previous_df, new_df):
    if previous_df is None or previous_df.empty:
        return new_df
    if new_df.empty:
        return previous_df
    changed_ids = set(new_df["project_id"])
    kept = previous_df[~previous_df["project_id"].isin(changed_ids)]
    return pd.concat([kept, new_df], ignore_index=True)

def merge_materials_table(previous_df, new_df, changed_project_ids):
    if previous_df is None or previous_df.empty:
        return new_df
    if not changed_project_ids:
        return previous_df
    kept = previous_df[~previous_df["project_id"].isin(changed_project_ids)]
    return pd.concat([kept, new_df], ignore_index=True)

def merge_services_table(previous_df, new_df):
    if previous_df is None or previous_df.empty:
        return new_df
    if new_df.empty:
        return previous_df
    changed_ids = set(new_df["subtask_id"])
    kept = previous_df[~previous_df["subtask_id"].isin(changed_ids)]
    return pd.concat([kept, new_df], ignore_index=True)

# --------------------------------------------
# Cleaning & Normalising tables
# --------------------------------------------
def split_clean_tables(cln_project_df, material_df, labor_df=None):
    # --- Define field types ---
    string_cols = [
        "project_name", "project_status",
        "client_name", "client_email_address",
        "client_street_name",
        "client_post_code", "client_outward_code",
        "client_inward_code", "client_city"
    ]
    numeric_cols = [
        "project_value", "dardan_days_worked", 
        "musa_days_worked", "dori_days_worked", 
        "remzi_days_worked"
    ]
    date_cols = ["project_start_date", "project_end_date"]

    # --- Fill missing values in projects ---
    for col in string_cols:
        if col in cln_project_df.columns:
            cln_project_df[col] = cln_project_df[col].fillna("N/A")
    for col in numeric_cols:
        if col in cln_project_df.columns:
            cln_project_df[col] = pd.to_numeric(cln_project_df[col], errors="coerce").fillna(0)
    for col in date_cols:
        if col in cln_project_df.columns:
            cln_project_df[col] = pd.to_datetime(cln_project_df[col], errors="coerce").dt.strftime("%Y-%m-%d")
            cln_project_df[col] = cln_project_df[col].fillna("N/A")

    # --- Client Dimension ---
    client_dim = cln_project_df[[
        "client_name",
        "sales_channel",
        "client_email_address",
        "client_phone_number",
        "client_street_name",
        "client_post_code",
        "client_outward_code",
        "client_inward_code",
        "client_city"
    ]].fillna("N/A")

    client_dim = client_dim.drop_duplicates(
        subset=["client_name", "client_email_address", "client_post_code"],
        keep="first"
    ).reset_index(drop=True)
    client_dim['client_numeric_id'] = client_dim.index + 1
    client_dim['client_id'] = client_dim['client_numeric_id'].apply(lambda x: f"C{x:03d}")
    client_dim.drop(columns=['client_numeric_id'], inplace=True)
    cols = ['client_id'] + [c for c in client_dim.columns if c != 'client_id']
    client_dim = client_dim[cols]

    # --- Project Dimension ---
    project_dim = cln_project_df[[
        "project_id",
        "project_name",
        "project_status",
        "project_start_date",
        "project_end_date",
        "client_name",
        "client_email_address",
        "client_post_code"
    ]].merge(
        client_dim[["client_id", "client_name", "client_email_address", "client_post_code"]],
        on=["client_name", "client_email_address", "client_post_code"],
        how="left"
    ).drop(columns=["client_name", "client_email_address", "client_post_code"])

    # --- Project Fact ---
    total_materials_fact = (
        material_df.groupby("project_id")
        .apply(lambda x: (x["expense_cost"].fillna(0) * x["quantity"].fillna(0)).sum())
        .reset_index(name="total_material_cost")
    )

    project_fact = cln_project_df[[
        "project_id", 
        "project_name",
        "project_value",
        "dardan_days_worked", 
        "musa_days_worked",
        "dori_days_worked", 
        "remzi_days_worked"
    ]].merge(total_materials_fact, on="project_id", how="left")

    # Fill missing numeric values in project_fact
    project_fact = project_fact.fillna({
        "project_value": 0,
        "dardan_days_worked": 0,
        "musa_days_worked": 0,
        "dori_days_worked": 0,
        "remzi_days_worked": 0,
        "total_material_cost": 0
    })

    # --- Material Fact ---
    material_fact = material_df.fillna({
        "expense_name": "N/A",
        "expense_cost": 0,
        "quantity": 0
    })

    # --- Labor Fact ---
    if labor_df is not None and not labor_df.empty:
        labor_fact = labor_df.rename(columns={
            "Date": "date_id",
            "Dardan Labor": "dardan_labor",
            "Musa Labor": "musa_labor",
            "Dori Labor": "dori_labor",
            "Daily Progress": "daily_progress"
        })
        labor_fact[["dardan_labor","musa_labor","dori_labor","daily_progress"]] = labor_fact[
            ["dardan_labor","musa_labor","dori_labor","daily_progress"]
        ].fillna(0)

        labor_fact["date_id"] = pd.to_datetime(labor_fact["date_id"], errors="coerce")
        labor_fact = labor_fact.dropna(subset=["date_id"])
        labor_fact["date_id"] = labor_fact["date_id"].dt.strftime("%Y%m%d").astype(int)
    else:
        labor_fact = pd.DataFrame()

    return client_dim, project_dim, project_fact, material_fact, labor_fact