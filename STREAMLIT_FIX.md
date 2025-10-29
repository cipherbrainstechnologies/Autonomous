# Streamlit Command Not Found - Fix Guide

## Problem
```
ERROR: The term 'streamlit' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

## Solution

The `streamlit` command is not in your PATH. Use `python -m streamlit` instead.

### Quick Fix - Updated Scripts

All run scripts have been updated to use `python -m streamlit` which works on all systems.

### Manual Run

Instead of:
```powershell
streamlit run dashboard/ui_frontend.py
```

Use:
```powershell
python -m streamlit run dashboard/ui_frontend.py
```

## Why This Happens

On Windows, when Python is installed, the Scripts directory (where `streamlit.exe` is located) may not be in your PATH. Using `python -m streamlit` uses Python's module execution system, which always works.

## Updated Commands

### PowerShell
```powershell
# Using the script (now fixed)
.\run_local.ps1

# Or direct command
python -m streamlit run dashboard/ui_frontend.py
```

### CMD
```cmd
# Using the script (now fixed)
.\run_local.bat

# Or direct command
python -m streamlit run dashboard/ui_frontend.py
```

### Linux/Mac
```bash
# Using the script (now fixed)
./run_local.sh

# Or direct command
python3 -m streamlit run dashboard/ui_frontend.py
```

## Alternative: Add to PATH (Optional)

If you want to use `streamlit` directly:

1. Find Python Scripts directory:
   ```
   C:\Python312\Scripts\  (or wherever Python is installed)
   ```

2. Add to PATH:
   - Open System Properties → Environment Variables
   - Edit PATH variable
   - Add: `C:\Python312\Scripts`
   - Restart PowerShell/terminal

3. Verify:
   ```powershell
   streamlit --version
   ```

But using `python -m streamlit` is recommended as it always works without PATH changes.

