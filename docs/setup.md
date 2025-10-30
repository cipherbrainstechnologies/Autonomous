# Setup Guide

## Prerequisites
- Python 3.11+
- Postgres 14+ (or managed)
- pip packages from requirements

## Environment

Set database URL (preferred via env):

```
# Postgres (Windows PowerShell example)
$env:DATABASE_URL = "postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME"
```

Alternatively, add to `config/secrets.toml`:

```
# Either top-level
database_url = "postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME"

# Or nested
[database]
url = "postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME"

[tenant]
org_id = "demo-org"
user_id = "admin"
```

## Feature Flags

```
[features]
use_csv_fallback = false
```

## Running

```
pip install -r requirements.txt
python -m streamlit run dashboard/ui_frontend.py
```

Ensure broker credentials are configured in `.streamlit/secrets.toml` per your provider.

