# main.py
from config import BESA_CLIENTS_LIST_ID
from extract import get_all_tasks, get_task_details, get_subtasks
from transform import build_projects_table, build_materials_table, build_services_table, build_labor_table, split_clean_tables, clean_project_addresses
from export import export_to_excel, export_clean_tables_to_excel, export_clean_tables_to_csv

if __name__ == "__main__":
    all_tasks = get_all_tasks(BESA_CLIENTS_LIST_ID)
    # paid_tasks = [t for t in all_tasks if t["status"]["status"].lower() == "paid invoice"]
    # ongoing_tasks = [t for t in all_tasks if t["status"]["status"].lower() == "ongoing"]
    detailed_tasks = get_task_details([t["id"] for t in all_tasks])
    subtasks = get_subtasks(BESA_CLIENTS_LIST_ID)


    raw_project_df = build_projects_table(detailed_tasks)
    cln_project_df = clean_project_addresses(raw_project_df)
    materials_df = build_materials_table(detailed_tasks)
    services_df = build_services_table(detailed_tasks,subtasks)
    # labor_df = build_labor_table(ongoing_tasks, existing_df=None)

    export_to_excel(cln_project_df, materials_df, services_df)

    
    client_dim, project_dim, project_fact, material_fact, labor_fact = split_clean_tables(
    cln_project_df, materials_df)

    export_clean_tables_to_excel(client_dim, project_dim, project_fact, material_fact)
    export_clean_tables_to_csv(client_dim, project_dim, project_fact, material_fact)