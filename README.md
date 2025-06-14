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
- `NOTION_TOKEN`
- `NOTION_DB_ID`

Run the handler:

```bash
python -m monday_secretary.main_handler
```
