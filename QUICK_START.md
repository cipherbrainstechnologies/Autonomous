# Quick Start Guide - Get Running in 5 Minutes

## Fast Track Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Credentials
```bash
python utils/generate_password_hash.py
```
Copy the generated hash and key.

### 3. Configure Secrets
Edit `.streamlit/secrets.toml` - paste your generated hash and key.

### 4. Verify Setup
```bash
python verify_setup.py
```

### 5. Run Dashboard
```powershell
# PowerShell (Recommended)
.\run_local.ps1

# Or direct command (works on all systems)
python -m streamlit run dashboard/ui_frontend.py
```

**Note**: Use `python -m streamlit` instead of just `streamlit` for better Windows compatibility.

### 6. Login
- Open browser at `http://localhost:8501`
- Use credentials from `secrets.toml`

## That's It! 🎉

Your dashboard should now be running locally with logging enabled.

## What Gets Logged?

- Application startup/shutdown
- Authentication attempts
- Errors and warnings
- Trade executions (when implemented)
- Backtest runs

All logs are saved to:
- **Console**: Real-time output
- **File**: `logs/errors.log` (persistent)

## Need More Details?

- Full setup guide: [LOCAL_RUN.md](LOCAL_RUN.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Main documentation: [README.md](README.md)

