# export.py
import pandas as pd
import os
from config import BASE_DIR, RAW_DATA_FILE

# Export table
def export_to_excel(cln_project_df, materials_df, services_df, filename=RAW_DATA_FILE):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        cln_project_df.to_excel(writer, sheet_name="Projects", index=False)
        materials_df.to_excel(writer, sheet_name="Materials", index=False)
        services_df.to_excel(writer, sheet_name="Services", index=False)
        # labor_df.to_excel(writer, sheet_name="Labor", index=False)
    #print(f"✅ Data exported to {filename}")
    print(filename)


def export_clean_tables_to_excel(
    client_dim,
    project_dim,
    project_fact,
    expense_fact,
    # daily_labor_fact,
    filename=BASE_DIR / "data" / "clean" / "besaconstruction_clean_data.xlsx"
):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        if client_dim is not None and not client_dim.empty:
            client_dim.to_excel(writer, sheet_name="ClientDim", index=False)
        if project_dim is not None and not project_dim.empty:
            project_dim.to_excel(writer, sheet_name="ProjectDim", index=False)
        if project_fact is not None and not project_fact.empty:
            project_fact.to_excel(writer, sheet_name="ProjectFact", index=False)
        if expense_fact is not None and not expense_fact.empty:
            expense_fact.to_excel(writer, sheet_name="ExpenseFact", index=False)
        # if daily_labor_fact is not None and not daily_labor_fact.empty:
        #     daily_labor_fact.to_excel(writer, sheet_name="DailyLaborFact", index=False)

    print(f"✅ Clean dimension/fact tables exported to {filename}")


def export_clean_tables_to_csv(
    client_dim,
    project_dim,
    project_fact,
    expense_fact,
    # daily_labor_fact,
    output_dir=BASE_DIR / "data" / "clean"
):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    if client_dim is not None and not client_dim.empty:
        client_dim.to_csv(os.path.join(output_dir, "ClientDim.csv"), index=False)
    print(f"✅ Clean ClientDim table exported as CSVs to {output_dir}")
    if project_dim is not None and not project_dim.empty:
        project_dim.to_csv(os.path.join(output_dir, "ProjectDim.csv"), index=False)
    print(f"✅ Clean ProjectDim table exported as CSVs to {output_dir}")
    if project_fact is not None and not project_fact.empty:
        project_fact.to_csv(os.path.join(output_dir, "ProjectFact.csv"), index=False)
    print(f"✅ Clean ProjectFact table exported as CSVs to {output_dir}")
    if expense_fact is not None and not expense_fact.empty:
        expense_fact.to_csv(os.path.join(output_dir, "ExpenseFact.csv"), index=False)
    print(f"✅ Clean ExpenseFact table exported as CSVs to {output_dir}")
    # if daily_labor_fact is not None and not daily_labor_fact.empty:
    #     daily_labor_fact.to_csv(os.path.join(output_dir, "DailyLaborFact.csv"), index=False)

