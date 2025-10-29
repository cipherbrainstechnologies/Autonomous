# TOML Parser Fix

## Issue
```
yaml.parser.ParserError: expected '<document start>', but found '<scalar>'
in ".streamlit/secrets.toml", line 6, column 1
```

## Problem
The code was trying to parse a TOML file (`secrets.toml`) using a YAML parser. TOML and YAML are different file formats:
- **TOML**: Uses `key = "value"` and `[section]` syntax
- **YAML**: Uses indentation and `key: value` syntax

## Solution

### 1. Updated `dashboard/ui_frontend.py`
- Added TOML parser import with fallbacks:
  - First tries `tomllib` (Python 3.11+ standard library)
  - Falls back to `tomli` package (Python < 3.11)
  - Last resort: `toml` package (older API)

- Changed `load_config()` function:
  - Switched from `yaml.load()` to `tomllib.load()`
  - Opens file in binary mode (`'rb'`) as required by TOML parsers

### 2. Updated `requirements.txt`
- Added `tomli` and `tomli-w` for Python < 3.11 compatibility
- Python 3.11+ uses built-in `tomllib` (no extra package needed)

## Code Changes

**Before**:
```python
import yaml
from yaml.loader import SafeLoader

with open(secrets_path, 'r') as file:
    config = yaml.load(file, Loader=SafeLoader)  # ❌ Wrong parser!
```

**After**:
```python
import tomllib  # or tomli/toml as fallback

with open(secrets_path, 'rb') as file:  # Binary mode
    config = tomllib.load(file)  # ✅ Correct parser!
```

## Installation

For Python < 3.11, install the TOML parser:
```powershell
pip install tomli tomli-w
```

For Python 3.11+, no additional installation needed (uses standard library).

## Verification

The dashboard should now load `secrets.toml` correctly. Run:
```powershell
.\run_local.ps1
```

Or:
```powershell
python -m streamlit run dashboard/ui_frontend.py
```

