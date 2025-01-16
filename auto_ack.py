import requests
import time
import random
from datetime import datetime
from typing import Dict, List

# OPTIONAL: COLOR CODES AND PRINT HELPERS
# ----------------------------------------------------------------------------

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"

def print_info(message: str) -> None:
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"{CYAN}[INFO {now_str}]{RESET} {message}")

def print_success(message: str) -> None:
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"{GREEN}[SUCCESS {now_str}]{RESET} {message}")

def print_warning(message: str) -> None:
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"{YELLOW}[WARNING {now_str}]{RESET} {message}")

def print_error(message: str) -> None:
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"{RED}[ERROR {now_str}]{RESET} {message}")
# ----------------------------------------------------------------------------


# CONFIGURATION
# ----------------------------------------------------------------------------
API_TOKEN: str = ""  # Replace with your actual API token
LIST_ID: str = ""  # Replace with the numeric ID of your ClickUp list

HEADERS: Dict[str, str] = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

# The range (in minutes) to wait before updating a found task
MIN_WAIT: int = 1
MAX_WAIT: int = 10

# How often (in seconds) the script should poll for new tasks
POLL_INTERVAL: int = 60

# The exact status strings in your ClickUp workflow
STATUS_TO_FIND: str = "to be reviewed"
STATUS_TO_SET: str = "acknowledged"
# ----------------------------------------------------------------------------


# FUNCTIONS
# ----------------------------------------------------------------------------
def get_tasks_in_review(list_id: str) -> List[Dict]:
    """
    Retrieves tasks from the specified ClickUp list that have status 'to be reviewed'.
    Returns a list of task dictionaries.
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
        return data.get("tasks", [])
    except requests.exceptions.RequestException as e:
        print_error(f"Error retrieving tasks: {e}")
        return []


def should_update_task(task_id: str) -> bool:
    """
    Checks if the task is still in the 'STATUS_TO_FIND' status before updating.
    
    :param task_id: The ID of the task to verify.
    :return: True if the task is still in STATUS_TO_FIND, False otherwise.
    """
    url = f"https://api.clickup.com/api/v2/task/{task_id}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        task_data = response.json()
        current_status = task_data.get("status", {}).get("status")

        if current_status == STATUS_TO_FIND:
            return True
        else:
            print_warning(
                f"Task {task_id} is no longer "
                f"'{STATUS_TO_FIND}' (current status: '{current_status}'). Skipping."
            )
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Error verifying task {task_id}: {e}")
        return False


def update_task_status(task_id: str, new_status: str) -> None:
    """
    Updates the status of a specified ClickUp task.
    """
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    payload = {"status": new_status}

    try:
        response = requests.put(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        print_success(f"Task {task_id} status updated to '{new_status}'.")
    except requests.exceptions.RequestException as e:
        print_error(f"Error updating task {task_id}: {e}")


# MAIN LOOP
# ----------------------------------------------------------------------------
def main() -> None:
    """
    Main loop that:
      1) Polls for tasks in 'to be reviewed' status.
      2) For each found task not in our 'acknowledgment queue', schedule an update time.
      3) Checks the queue for tasks whose scheduled time has come, then updates them
         (verifying they are still in 'to be reviewed' before updating).
      4) Sleeps for the poll interval before checking again.
    """

    # Optional fancy banner:
    print(MAGENTA + "=" * 60 + RESET)
    print(MAGENTA + "         Welcome to the ClickUp Task Watcher!         " + RESET)
    print(MAGENTA + "=" * 60 + RESET)

    print_info("Initializing the acknowledgment queue...")
    acknowledgment_queue: Dict[str, float] = {}

    while True:
        print_info(f"Polling for tasks with status '{STATUS_TO_FIND}'...")

        tasks_in_review = get_tasks_in_review(LIST_ID)

        # Add newly discovered tasks to the queue
        for task in tasks_in_review:
            task_id = task["id"]
            if task_id not in acknowledgment_queue:
                wait_minutes = random.randint(MIN_WAIT, MAX_WAIT)
                schedule_time = time.time() + (wait_minutes * 60)
                acknowledgment_queue[task_id] = schedule_time
                print_info(
                    f"  Found task {task_id}. "
                    f"Scheduled to acknowledge in {wait_minutes} minute(s)."
                )

        # Process tasks that are ready to be updated
        tasks_to_remove: List[str] = []
        current_time = time.time()
        for task_id, scheduled_time in acknowledgment_queue.items():
            if current_time >= scheduled_time:
                if should_update_task(task_id):
                    update_task_status(task_id, STATUS_TO_SET)
                # Remove from queue after attempt
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            acknowledgment_queue.pop(task_id, None)

        print_info(f"Sleeping for {POLL_INTERVAL} second(s) before the next poll...\n")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
