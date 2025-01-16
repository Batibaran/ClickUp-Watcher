import requests
import time
import random
from datetime import datetime  # for printing current time

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
POLL_INTERVAL = 60  # 1 minute

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
      1) Polls for tasks in 'to be reviewed' status.
      2) For each found task not in our 'acknowledgment queue', schedule an update time
         (current time + random(1-15) minutes).
      3) Checks the queue for tasks whose scheduled time has come, then updates them.
      4) Sleeps for the poll interval before checking again.
    """
    print("Starting ClickUp Task Watcher...")

    # Dictionary to track tasks that need to be acknowledged.
    acknowledgment_queue = {}

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Polling for tasks with status '{STATUS_TO_FIND}'...")

        tasks_in_review = get_tasks_in_review(LIST_ID)

        # Add new tasks to the queue if they're not already in it
        for task in tasks_in_review:
            task_id = task["id"]
            if task_id not in acknowledgment_queue:
                wait_minutes = random.randint(MIN_WAIT, MAX_WAIT)
                scheduled_time = time.time() + (wait_minutes * 60)
                acknowledgment_queue[task_id] = scheduled_time
                print(f"  Found task {task_id}. Scheduled to acknowledge in {wait_minutes} minute(s).")

        # Check which tasks are ready to be acknowledged
        tasks_to_remove = []
        current_time = time.time()
        for task_id, scheduled_time in acknowledgment_queue.items():
            if current_time >= scheduled_time:
                update_task_status(task_id, STATUS_TO_SET)
                tasks_to_remove.append(task_id)

        # Remove acknowledged tasks from the queue
        for task_id in tasks_to_remove:
            del acknowledgment_queue[task_id]

        # Sleep for the poll interval before checking again
        print(f"Sleeping {POLL_INTERVAL} second(s) before next poll...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
