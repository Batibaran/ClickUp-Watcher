import requests
import time
import random


# CONFIGURATION
# ----------------------------------------------------------------------------
API_TOKEN = ""  # Replace with your actual API token
LIST_ID = ""  # Replace with the numeric ID of your ClickUp list

HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

# The range (in minutes) to wait before updating a found task
MIN_WAIT = 1
MAX_WAIT = 10

# How often (in seconds) the script should poll for new tasks
POLL_INTERVAL = 60

# The exact status strings in your ClickUp workflow
STATUS_TO_FIND = "to be reviewed"
STATUS_TO_SET = "acknowledged"
# ----------------------------------------------------------------------------


# FUNCTIONS
# ----------------------------------------------------------------------------
def get_tasks_in_review(list_id):
    """
    Retrieves tasks from the specified ClickUp list that have status 'to be reviewed'.
    Returns a list of tasks (dictionaries).
    """
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

    params = {
        "statuses[]": [STATUS_TO_FIND],
        "archived": "false"
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        tasks = data.get("tasks", [])
        return tasks
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving tasks: {e}")
        return []


def update_task_status(task_id, new_status):
    """
    Updates the status of a specified ClickUp task.

    :param task_id: The ID of the task to update.
    :param new_status: The new status to apply to the task.
    """
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    payload = {
        "status": new_status
    }

    try:
        response = requests.put(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        print(f"Successfully updated task {task_id} to status '{new_status}'.")
    except requests.exceptions.RequestException as e:
        print(f"Error updating task {task_id}: {e}")
# ----------------------------------------------------------------------------


# MAIN LOOP
# ----------------------------------------------------------------------------
def main():
    """
    Main loop that:
      1) Polls for tasks in 'to be reviewed' status,
      2) For each found task, waits 1-10 minutes, then
      3) Updates the task to 'acknowledged'.
    """
    print("Starting ClickUp Task Watcher...")

    while True:
        print(f"\nPolling for tasks with status '{STATUS_TO_FIND}'...")

        tasks_in_review = get_tasks_in_review(LIST_ID)

        if not tasks_in_review:
            print(f"No tasks in '{STATUS_TO_FIND}' status found.")
        else:
            for task in tasks_in_review:
                task_id = task["id"]

                wait_minutes = random.randint(MIN_WAIT, MAX_WAIT)
                print(f"Found task: {task_id}. Waiting {wait_minutes} minute(s) before updating.")

                time.sleep(wait_minutes * 60)

                update_task_status(task_id, STATUS_TO_SET)

        print(f"Sleeping {POLL_INTERVAL} second(s) before next check...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
