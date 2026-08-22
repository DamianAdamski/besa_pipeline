# extract.py
from api import clickup_get
from config import HEADERS

PAGE_SIZE = 100  # ClickUp caps "list tasks" responses at 100 tasks per page

def _get_all_task_pages(list_id, extra_params=None):
    #Fetch every page of tasks for a list, following ClickUp's pagination.
    tasks = []
    page = 0
    while True:
        params = {"page": page}
        if extra_params:
            params.update(extra_params)
        response = clickup_get(f"list/{list_id}/task", HEADERS, params=params)
        page_tasks = response.get("tasks", [])
        tasks.extend(page_tasks)

        last_page = response.get("last_page")
        if last_page is None:
            last_page = len(page_tasks) < PAGE_SIZE
        if last_page or not page_tasks:
            break
        page += 1
    return tasks

def get_all_tasks(list_id, date_updated_gt=None):
    # to return all invoices (or, with date_updated_gt set, only those changed since that ms-epoch timestamp)
    extra_params = {"date_updated_gt": date_updated_gt} if date_updated_gt else None
    return _get_all_task_pages(list_id, extra_params=extra_params)

def get_task_details(task_ids):
    details = []
    for task_id in task_ids:
        details.append(clickup_get(f"task/{task_id}", HEADERS))
    return details

def get_subtasks(list_id, date_updated_gt=None):
    extra_params = {"subtasks": "true"}
    if date_updated_gt:
        extra_params["date_updated_gt"] = date_updated_gt
    tasks_with_subtasks = _get_all_task_pages(list_id, extra_params=extra_params)
    return [task for task in tasks_with_subtasks if task.get("parent")]

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