# extract.py
from api import clickup_get
from config import HEADERS

def get_all_tasks(list_id):
    tasks = clickup_get(f"list/{list_id}/task", HEADERS)["tasks"]
    # to return all invoices
    return [t for t in tasks] 

def get_task_details(task_ids):
    details = []
    for task_id in task_ids:
        details.append(clickup_get(f"task/{task_id}", HEADERS))
    return details

def get_subtasks(list_id):
    subtasks = []
    tasks_with_subtasks = clickup_get(
        f"list/{list_id}/task",
        HEADERS,
        params={"subtasks": "true"}
    )["tasks"]
    for task in tasks_with_subtasks:
        if task.get("parent"):  # this task is a subtask
            subtasks.append(task)
    return subtasks

def get_task_texts(tasks):
    """
    Retrieves the 'text_content' (or fallback 'description')
    for ALL tasks in the list.
    Returns a dict {task_id: text_content}.
    """
    results = {}
    for task in tasks:
        text = task.get('text_content') or task.get('description') or ""
        results[task['id']] = text
    return results

import pandas as pd

def labor_text_to_table(labor_text, task_id):
    """
    Converts labor activity text into a structured DataFrame.
    Assumes format:
        Date
        Dardan Labor
        Musa Labor
        Dori Labor
        Daily Progress
        <rows in multiples of 5>
    """
    # Split lines and remove empty lines
    lines = [line.strip() for line in labor_text.splitlines() if line.strip()]

    if len(lines) < 6:
        return pd.DataFrame()  # not enough data to form a table

    # Header
    header = lines[:5]
    rows = lines[5:]

    # Group rows by 5
    data = [rows[i:i+5] for i in range(0, len(rows), 5)]

    # Build DataFrame
    df = pd.DataFrame(data, columns=header)

    # Clean strings
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Attach project_id
    df["project_id"] = task_id

    return df