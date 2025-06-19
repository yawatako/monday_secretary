# Monday Secretary

A lightweight toolkit for integrating Google Sheets, Google Calendar, and Notion to assist with weekly planning.

## Local setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with the following variables:

- `GOOGLE_SA_JSON_PATH`
- `GOOGLE_CAL_SA_JSON_PATH` (optional)
- `SHEET_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_TASKS_REFRESH_TOKEN`
- `GOOGLE_TASKS_LIST_ID` (optional, default `@default`)
- `NOTION_TOKEN`
- `NOTION_DB_ID`

Run the handler:

```bash
python -m monday_secretary.main_handler
```

### Quick API test

```bash
curl https://<your-service>.onrender.com/healthcheck
curl -X POST -H "Content-Type: application/json" \
     -d '{"user_msg":"おはよう、体調どう？"}' \
     https://<your-service>.onrender.com/chat
curl -X POST -H "Content-Type: application/json" \
     -d '{"title":"眠い","summary":"会議中にウトウトした"}' \
     http://localhost:8000/memory
# Only `title` and `summary` are required. Other fields will be filled with
# sensible defaults by the API.
curl -X POST -H "Content-Type: application/json" \
     -d '{"action":"list"}' \
    http://localhost:8000/tasks
```

### Weekend cleanup

Running `handle_message("週末整理して")` will collect this week's events,
unfinished tasks, health logs and work summaries. It helps review progress
before planning the next week.

### Google Tasks client example

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

creds = Credentials(
    None,
    refresh_token=os.getenv("GOOGLE_TASKS_REFRESH_TOKEN"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scopes=["https://www.googleapis.com/auth/tasks"],
)

service = build("tasks", "v1", credentials=creds)
print(service.tasklists().list().execute())
```

### Client utilities

Each API client inherits from `BaseClient` which provides a helper
method for running blocking SDK calls in a background thread. All network
operations share the same retry logic via the `DEFAULT_RETRY` decorator.

### Error responses

When an internal error occurs, the API returns a JSON body like:

```json
{"detail": "<exception message>"}
```

This helps with debugging failing requests.
