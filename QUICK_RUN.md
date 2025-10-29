# Quick Run Guide - PowerShell

## Running on Windows (PowerShell)

### Option 1: PowerShell Script (Recommended)
```powershell
.\run_local.ps1
```

### Option 2: Batch File (CMD)
```cmd
.\run_local.bat
```

### Option 3: Direct Streamlit
```powershell
# Use python -m streamlit (works on all systems)
python -m streamlit run dashboard/ui_frontend.py
```

## Common PowerShell Errors & Solutions

### Error: "Execution Policy"
If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "Cannot run script"
Run PowerShell as Administrator or use:
```powershell
powershell -ExecutionPolicy Bypass -File .\run_local.ps1
```

### Error: "Python not found"
Make sure Python is in your PATH:
```powershell
# Check Python
python --version

# If not found, add Python to PATH or use full path:
C:\Python312\python.exe -m streamlit run dashboard/ui_frontend.py
```

## Verify Setup First

Before running, verify everything is set up:
```powershell
python verify_setup.py
```

This will check:
- ✅ Python version
- ✅ Dependencies
- ✅ Configuration files
- ✅ Directory structure

## Step-by-Step (PowerShell)

1. **Open PowerShell in project directory**
   ```powershell
   cd "f:\Projects\Github Projects\Autonomous"
   ```

2. **Verify setup**
   ```powershell
   python verify_setup.py
   ```

3. **Install dependencies (if needed)**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run dashboard**
   ```powershell
   .\run_local.ps1
   ```
   OR
   ```powershell
   python -m streamlit run dashboard/ui_frontend.py
   ```

## Troubleshooting

### Python path issues
If Python is not found, specify full path:
```powershell
C:\Python312\python.exe verify_setup.py
C:\Python312\python.exe -m streamlit run dashboard/ui_frontend.py
```

### Import errors
Ensure you're in the project root directory:
```powershell
Get-Location  # Should show: f:\Projects\Github Projects\Autonomous
```

### Module not found
Install missing packages:
```powershell
pip install streamlit streamlit-authenticator pandas numpy pyyaml
```

## Logs Location

- Console output: Shows in PowerShell window
- File logs: `logs/errors.log`
- Trade logs: `logs/trades.csv`

