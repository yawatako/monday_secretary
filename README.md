# Monday Secretary

A lightweight toolkit for integrating Google Sheets, Google Calendar, and Notion to assist with weekly planning.

## Local setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with the following variables:

- `GOOGLE_SA_JSON_PATH`
- `SHEET_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_TASKS_CLIENT_ID`
- `GOOGLE_TASKS_CLIENT_SECRET`
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

### Client utilities

Each API client inherits from `BaseClient` which provides a helper
method for running blocking SDK calls in a background thread. All network
operations share the same retry logic via the `DEFAULT_RETRY` decorator.

### Error handling

All unhandled exceptions and validation errors are logged with stack traces.
The API responds with HTTP 500 or 422 respectively.
