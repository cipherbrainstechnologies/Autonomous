# Local Run Guide - NIFTY Options Trading System

## Prerequisites Check

Before running, ensure you have:

1. **Python 3.10 or higher**
   ```bash
   python --version
   ```

2. **All dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

## Step-by-Step Local Setup

### Step 1: Generate Authentication Credentials

Generate password hash and cookie key:

```bash
python utils/generate_password_hash.py
```

This will output:
- Password hash (add to `secrets.toml`)
- Cookie key (add to `secrets.toml`)

### Step 2: Configure Secrets

Edit `.streamlit/secrets.toml` with your generated credentials:

```toml
[credentials]
names = ["Your Name"]
usernames = ["admin"]
passwords = ["$2b$12$YOUR_GENERATED_HASH_HERE"]

[cookie]
name = "nifty_auth"
key = "YOUR_GENERATED_KEY_HERE"
expiry_days = 30

[broker]
type = "angel"  # or "fyers"
api_key = "YOUR_API_KEY"
access_token = "YOUR_ACCESS_TOKEN"
client_id = "YOUR_CLIENT_ID"
api_secret = "YOUR_API_SECRET"
```

**Note**: For local testing, you can use placeholder broker credentials if you don't have real API keys yet.

### Step 3: Verify Configuration

Check that `config/config.yaml` exists and has valid values:

```bash
cat config/config.yaml
```

### Step 4: Initialize Application

Initialize the application (creates required directories and files):

```bash
python main.py
```

This should output:
```
==================================================
NIFTY Options Trading System
==================================================

To start the dashboard, run:
  streamlit run dashboard/ui_frontend.py

Or for development:
  python main.py
==================================================
```

### Step 5: Run Dashboard

**Option A: Direct Streamlit Run (Recommended)**

```powershell
# PowerShell/CMD - Use python -m streamlit
python -m streamlit run dashboard/ui_frontend.py

# Linux/Mac
python3 -m streamlit run dashboard/ui_frontend.py
```

**Note**: Use `python -m streamlit` instead of just `streamlit` for better Windows compatibility.

**Option B: Using Run Script (with logging)**

```powershell
# PowerShell (Recommended)
.\run_local.ps1

# Windows CMD
.\run_local.bat

# Linux/Mac
chmod +x run_local.sh
./run_local.sh
```

### Step 6: Access Dashboard

The dashboard will automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, navigate to the URL manually.

### Step 7: Login

Use the credentials from `secrets.toml`:
- **Username**: The username you configured
- **Password**: The original password (before hashing)

## Verification Checklist

### ✅ Application Initialization
- [ ] `python main.py` runs without errors
- [ ] All directories are created (logs/, engine/, dashboard/, etc.)
- [ ] `logs/trades.csv` has header row

### ✅ Dependencies
- [ ] All packages install without errors: `pip install -r requirements.txt`
- [ ] Python version is 3.10 or higher

### ✅ Configuration
- [ ] `.streamlit/secrets.toml` exists and is properly formatted
- [ ] `config/config.yaml` exists with valid parameters
- [ ] Password hash is generated and added to secrets.toml

### ✅ Dashboard Launch
- [ ] Streamlit starts without errors
- [ ] Browser opens to `http://localhost:8501`
- [ ] Login page appears

### ✅ Authentication
- [ ] Can login with configured credentials
- [ ] Dashboard loads after successful login
- [ ] Logout button works

### ✅ Dashboard Tabs
- [ ] **Dashboard Tab**: Shows algo status, broker info
- [ ] **Trade Journal Tab**: Loads (may be empty initially)
- [ ] **Backtest Tab**: Shows upload interface
- [ ] **Settings Tab**: Shows configuration

### ✅ Logging
- [ ] `logs/errors.log` is created and logs errors
- [ ] Application logs appear in console
- [ ] Trade logging works (when trades are executed)

## Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution**: Install missing dependencies
```bash
pip install -r requirements.txt
```

### Issue: "secrets.toml not found"

**Solution**: Ensure `.streamlit/secrets.toml` exists:
```bash
# Check if file exists
ls .streamlit/secrets.toml

# If not, create it from template
# Edit the template values in .streamlit/secrets.toml
```

### Issue: "Invalid credentials" on login

**Solution**: 
1. Verify password hash is correct in `secrets.toml`
2. Regenerate password hash: `python utils/generate_password_hash.py`
3. Ensure cookie key is properly set

### Issue: "Port 8501 already in use"

**Solution**: Streamlit will automatically use the next available port (8502, 8503, etc.)
- Check console output for the actual URL
- Or specify a different port: `streamlit run dashboard/ui_frontend.py --server.port=8502`

### Issue: Import errors from engine modules

**Solution**: Ensure you're running from the project root directory:
```bash
# Should be in: f:\Projects\Github Projects\Autonomous\
pwd  # Check current directory
cd ..  # Navigate to project root if needed
```

### Issue: Broker connection fails

**Solution**: For local testing, placeholder broker implementations are fine. Real API integration requires:
1. Valid broker API credentials
2. Full broker SDK implementation
3. Testing in sandbox/paper trading mode first

## Testing Workflow

1. **Start Application**: `streamlit run dashboard/ui_frontend.py`
2. **Login**: Use your configured credentials
3. **Check Dashboard Tab**: Verify status indicators
4. **Check Trade Journal**: Should load (empty initially is OK)
5. **Test Backtest Tab**: Upload sample CSV (optional)
6. **Check Settings**: Verify configuration display
7. **Review Logs**: Check `logs/errors.log` for any issues

## Sample Test Data for Backtesting

Create a sample CSV file `data/historical/sample_nifty.csv`:

```csv
Date,Open,High,Low,Close,Volume
2024-01-01,21500,21550,21480,21520,1000000
2024-01-02,21520,21580,21500,21560,1100000
...
```

Use this to test the backtest functionality.

## Quick Verification Script

Run the verification script to check all setup:

```powershell
# PowerShell
python verify_setup.py

# Or from CMD
python verify_setup.py
```

This will check:
- Python version
- Installed dependencies
- Directory structure
- Required files
- Configuration validity
- Secrets setup

**Note**: The script now works correctly in PowerShell and Windows CMD. It uses ASCII-safe characters for Windows compatibility.

## Next Steps After Local Verification

Once local run is successful:

1. **Configure Real Broker API** (if available)
2. **Test with Paper Trading** (recommended)
3. **Upload Historical Data** for backtesting
4. **Monitor Logs** for any issues
5. **Deploy to Cloud** (Render.com or other platform)

## Log Files Location

- **Application Logs**: `logs/errors.log`
- **Trade Logs**: `logs/trades.csv`
- **Console Output**: Check terminal/command prompt

## Performance Notes

- First startup may take a few seconds (module loading)
- Dashboard refresh happens automatically on interaction
- Large backtest datasets may take time to process

