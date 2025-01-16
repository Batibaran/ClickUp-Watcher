# ClickUp Task Watcher

This Python script periodically polls a specified [ClickUp](https://clickup.com/) list for tasks that are in the **to be reviewed** status, waits a random amount of time (1–10 minutes), and then updates those tasks to the **acknowledged** status. This script is useful if you want to automate a workflow step in ClickUp.

---

## Features

- Polls ClickUp for tasks in a specific status.
- Automatically updates tasks to a new status after a randomized waiting period.
- Simple, straightforward configuration.
- Runs continuously and polls at a configurable interval.

---

## Prerequisites

- **Python 3.6+** (recommended Python 3.7 or higher)
- [Requests library](https://docs.python-requests.org/) (installed via `pip install requests`)
