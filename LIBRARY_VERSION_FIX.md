# Library Version Issue - Password Validation Bug

## Problem

The error `string indices must be integers, not 'str' please hash all plain text passwords` occurs during password validation when submitting the login form, even with `auto_hash=True` and plain text passwords.

## Root Cause

This appears to be a bug in certain versions of `streamlit-authenticator` where the library's internal password validation logic incorrectly handles the credentials structure.

## Solution Options

### Option 1: Downgrade Library Version

Try using an older, more stable version:

```powershell
pip uninstall streamlit-authenticator -y
pip install streamlit-authenticator==0.2.2
```

Then restart your Streamlit app.

### Option 2: Upgrade to Latest Version

Sometimes newer versions fix bugs:

```powershell
pip install --upgrade streamlit-authenticator
```

### Option 3: Clear Streamlit Cache

The library might be caching old credentials:

```powershell
# Stop Streamlit
# Delete .streamlit/cache/ directory if it exists
# Restart Streamlit
```

### Option 4: Alternative Authentication

If the library continues to have issues, consider:

1. **Custom Authentication**: Implement simple username/password check using bcrypt directly
2. **Different Library**: Use a different Streamlit authentication library
3. **Session-based**: Use Streamlit's session state with custom login logic

## Check Current Version

```powershell
pip show streamlit-authenticator
```

## Recommendation

Try **Option 1** first (downgrade to 0.2.2), as version 0.2.3+ may have introduced the bug.

