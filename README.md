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

### Quick API test

```bash
curl https://<your-service>.onrender.com/healthcheck
curl -X POST -H "Content-Type: application/json" \
     -d '{"user_msg":"おはよう、体調どう？"}' \
     https://<your-service>.onrender.com/chat
curl -X POST -H "Content-Type: application/json" \
     -d '{"title":"眠い","summary":"会議中にウトウトした"}' \
     http://localhost:8000/memory
```
