# Immediate Fix - Library Version Issue

## Problem

You're using `streamlit-authenticator` version **0.4.2** which has a bug with password validation. This causes:
```
string indices must be integers, not 'str' please hash all plain text passwords
```

## Solution: Try Older Version

I'm installing version **0.2.3** which may not have this bug:

```powershell
pip install streamlit-authenticator==0.2.3 --force-reinstall
```

## After Installing

1. **Restart your Streamlit app completely**
   - Stop the current Streamlit process (Ctrl+C)
   - Restart with: `python -m streamlit run dashboard/ui_frontend.py`

2. **Clear browser cache** (optional but recommended)
   - Clear cookies for localhost:8501
   - Or use incognito/private mode

3. **Try logging in again**
   - Username: `admin`
   - Password: `admin`

## If That Doesn't Work

We'll implement a custom authentication bypass that doesn't use the library's login widget, but instead uses direct password checking with bcrypt.

