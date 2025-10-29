# Authentication Setup Fix

## Issue
```
❌ Authentication setup failed: list indices must be integers or slices, not str
```

## Problem
The `streamlit-authenticator` library API changed. The `Authenticate` constructor now expects:
- **Full credentials dictionary** (not individual lists)
- **Named parameters** (not positional arguments)

## Old API (Incorrect)
```python
authenticator = stauth.Authenticate(
    config['credentials']['names'],      # ❌ Individual list
    config['credentials']['usernames'],   # ❌ Individual list
    config['credentials']['passwords'],   # ❌ Individual list
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)
```

## New API (Correct)

The library expects credentials in **dict format** where each username is a key:

```python
# Convert from TOML list format to dict format
credentials_dict = {
    'usernames': {'admin': 'Admin'},      # {username: name}
    'names': {'admin': 'Admin'},          # {username: name}
    'passwords': {'admin': '$2b$12$...'}  # {username: password_hash}
}

authenticator = stauth.Authenticate(
    credentials=credentials_dict,         # ✅ Dict format
    cookie_name=config['cookie']['name'],       # ✅ Named parameter
    cookie_key=config['cookie']['key'],         # ✅ Named parameter
    cookie_expiry_days=float(config['cookie']['expiry_days']),  # ✅ Named parameter
    auto_hash=False  # ✅ Passwords already hashed
)
```

**Conversion Code**:
```python
# TOML format: names=["Admin"], usernames=["admin"], passwords=["hash"]
# Convert to: usernames={"admin": "Admin"}, passwords={"admin": "hash"}
credentials_dict = {
    'usernames': {},
    'names': {},
    'passwords': {}
}

for i, username in enumerate(usernames_list):
    credentials_dict['usernames'][username] = names_list[i]
    credentials_dict['names'][username] = names_list[i]
    credentials_dict['passwords'][username] = passwords_list[i]
```

## Changes Made

1. **Pass full credentials dict**: `credentials=config['credentials']`
2. **Use named parameters**: `cookie_name=`, `cookie_key=`, `cookie_expiry_days=`
3. **Convert expiry_days to float**: `float(config['cookie']['expiry_days'])`
4. **Set auto_hash=False**: Since passwords are pre-hashed in secrets.toml
5. **Added exception traceback**: For better debugging

## Verification

The authentication setup should now work correctly with the TOML configuration format.

## Related Files
- `dashboard/ui_frontend.py` - Updated authentication initialization
- `.streamlit/secrets.toml` - Credentials configuration (TOML format)

