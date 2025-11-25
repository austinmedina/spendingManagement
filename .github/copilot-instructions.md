**Purpose**
- **Goal**: Help AI coding agents become productive quickly in this Flask-based Receipt Tracker project.

**Overview**
- **App entrypoint**: `receipt-tracker-app.py` — a single-file Flask app that wires routes, CSV-backed storage, and Azure receipt analysis.
- **Auth**: `auth.py` — CSV-backed users with SHA256 password hashing, reset codes and email support (SMTP env vars).
-- **Storage modes**: Default CSV files (stored in the `csv/` directory). Optional PostgreSQL support implemented in `database.py` / `database-module.py` (swap CSV code paths when USE_CSV=false).
- **UI**: Jinja templates in `templates/` (base layout at `templates/base.html`) with Bootstrap + Chart.js.
- **File storage**: temporary uploads to `uploads/` then moved to `receipts/` with filenames stored in CSVs.
- **External integration**: Azure Document Intelligence via `analyze_receipt_with_azure` in `receipt-tracker-app.py` (controlled by `AZURE_DOC_INTELLIGENCE_*` env vars).

**How to run (dev)**
- **Create venv & install**: `python -m venv venv` then `.
  venv\Scripts\Activate.ps1` and `pip install -r requirements.txt`.
- **Run**: `python receipt-tracker-app.py` (app runs on `http://0.0.0.0:5000` by default).
- **ENV**: Put secrets in a `.env` file (project uses `python-dotenv`). Key examples:
  - `SECRET_KEY`, `USE_CSV=true|false`
  - `AZURE_DOC_INTELLIGENCE_ENDPOINT`, `AZURE_DOC_INTELLIGENCE_KEY`
  - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`
- **Switching to DB**: Set `USE_CSV=false`, configure DB env vars (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`), install `psycopg2-binary` and adapt routes in `receipt-tracker-app.py` to call `database.py` helpers instead of CSV helpers.

**Project-specific conventions & patterns**
- **CSV schema**: `CSV_HEADERS` in `receipt-tracker-app.py` is authoritative — maintain those column names when adding fields.
- **ID types**: IDs are stored as strings in CSVs (e.g., `'1'`) — new rows use `get_next_id()`.
- **Boolean flags**: stored as `'true'`/`'false'` strings in CSVs (not Python bools).
-- **Groups**: `csv/groups.csv`'s `members` column is a comma-separated string of usernames; use `get_person_groups()` utilities.
- **Splits**: Splits use a `receipt_group_id` to associate multiple transaction rows to one uploaded receipt.
- **Dates**: Use `YYYY-MM-DD` format consistently (many functions expect this).

**Security / auth notes**
- `auth.py` stores password hashes using SHA256 (`hash_password`) — when modifying auth flows keep existing hash function compatibility or migrate carefully.
- The app enforces `must_change_password` on login; do not bypass this check in decorators.

**When editing or adding routes**
- Use the decorators `@login_required` and `@admin_required` from `auth.py` as appropriate.
- Persist via helper functions: `read_csv`, `write_csv_row`, `rewrite_csv`, `get_next_id` to respect current CSV conventions.
- Enforce access using `filter_by_person_access()` for endpoints that return user data.

**Integration points & infra**
- Azure: `receipt-tracker-app.py::analyze_receipt_with_azure()` — stubbed when env vars absent; preserve logic for local dev fallback (sample parsed items).
- SMTP: `auth.py::send_reset_email()` — falls back to console output when SMTP not configured (useful for CI/dev).
- Cron/workers: `process_recurring_transactions()` runs on dashboard load; a production deployment could move this logic to a scheduled job using `/api/admin/run-notifications` or a custom runner.

**Devops / deployment caveats**
- The filename `receipt-tracker-app.py` contains hyphens and is not importable as a Python module for Gunicorn. For WSGI deployments either rename the file to a valid module name (recommended) or run via a wrapper script. Dev run: `python receipt-tracker-app.py`.
- `requirements.txt` comments out `psycopg2-binary` — add it when switching to PostgreSQL.

**Quick examples (do this in edits)**
- Add a new transaction field:
  1. Add the column name to `CSV_HEADERS['transactions']`.
  2. Update any `read_csv` consumers to handle the new key.
  3. Update write paths (use `write_csv_row`) and templates consuming that field.
- Add an auth-protected API route: decorate with `@login_required`, use `get_current_user()` or `get_current_person()` and return JSON.

**Where to look for reference**
- Routes, CSV handling, and business logic: `receipt-tracker-app.py` (most of the app).
- Auth flows and email: `auth.py`.
- Optional production DB helpers: `database.py` and `database-module.py`.
- Templates/UI patterns: `templates/base.html` and the page-specific templates in `templates/`.

If anything important is missing or you'd like a different level of detail (for example: example `.env`, WSGI wrapper, or an automated DB migration script), tell me which piece to add and I'll update this file.
