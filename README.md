# BESA Construction Data Pipeline

This project is a Python-based tool that collects project data from **ClickUp** and converts it into clean, structured tables for reporting and analysis. It handles projects, materials, services, and labor logs, and exports them to Excel and CSV files.

---

## Key Benefits

- Automatically fetches project data from ClickUp  
- Organizes and cleans data for easier analysis  
- Generates ready-to-use Excel and CSV reports  
- Saves time and reduces manual data entry errors  

---

## How It Works

1. **Extract:** Gets all tasks and subtasks from ClickUp, including custom fields and labor logs.  
2. **Transform:** Cleans and organizes the data into structured tables:
   - Projects  
   - Materials  
   - Services  
   - Labor (daily logs)  
3. **Load / Export:** Saves the cleaned data into Excel and CSV files.

---

## Output Files

**Raw Data (Excel):** `data/raw/raw_data.xlsx`

| Sheet     | Description |
|-----------|-------------|
| Projects  | Basic project details (client, status, dates, etc.) |
| Materials | Materials used with costs and quantities |
| Services  | Services performed with prices and descriptions |

**Cleaned Data (Excel & CSV):** `data/clean/besaconstruction_clean_data.xlsx`

| Table       | Description |
|-------------|-------------|
| ClientDim   | Clean client information |
| ProjectDim  | Project details linked to clients |
| ProjectFact | Project metrics including total cost |
| ExpenseFact | Material and service costs |

---

## How to Use

1. Clone the repository:

```bash
git clone https://github.com/yourusername/besa_pipeline.git
cd besa_pipeline
```

2. Install Python dependencies:
```pip install -r requirements.txt```

3. Find your API from ClickUp and create a file in the project folder called .env as below:

CLICKUP_TOKEN = YOUR_CLICKUP_TOKEN

4. Run the pipeline in your terminal ```python main.py```

6. Check the folders for the output files:
Raw Excel: data/raw/raw_data.xlsx
Cleaned Excel: data/clean/besaconstruction_clean_data.xlsx
Cleaned CSV: data/clean/*.csv


PROJECT STRUCTURE
besa_pipeline/
├─ data/
│  ├─ raw/       # Raw Excel exports
│  └─ clean/     # Cleaned Excel and CSV exports
├─ extract.py    # Fetch tasks and subtasks from ClickUp
├─ transform.py  # Clean and organize the data
├─ export.py     # Save data to Excel/CSV
├─ api.py        # ClickUp API helper
├─ config.py     # API keys and list IDs
├─ main.py       # Runs the full pipeline
└─ README.md     # This file




