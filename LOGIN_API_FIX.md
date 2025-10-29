# Login/Logout API Fix

## Issue
```
ValueError: Location must be one of 'main' or 'sidebar' or 'unrendered'
```

## Problem
The `streamlit-authenticator` API changed. The `login()` and `logout()` methods now use **named parameters** instead of positional arguments.

## Old API (Incorrect)
```python
# Old way - positional arguments
name, auth_status, username = authenticator.login("Login", "main")
authenticator.logout("Logout", "sidebar")
```

## New API (Correct)

### Login Method
```python
# New way - named parameters
name, auth_status, username = authenticator.login(
    location='main',      # First parameter: location
    key='Login'           # Named parameter: button key
)
```

### Logout Method
```python
# New way - named parameters
authenticator.logout(
    location='sidebar',  # First parameter: location
    key='Logout'         # Named parameter: button key
)
```

## Method Signatures

### login()
```python
login(
    location: Literal['main', 'sidebar', 'unrendered'] = 'main',
    key: str = 'Login',
    max_concurrent_users: Optional[int] = None,
    max_login_attempts: Optional[int] = None,
    # ... other optional parameters
) -> Optional[Tuple[Optional[str], Optional[bool], Optional[str]]]
```

### logout()
```python
logout(
    location: Literal['main', 'sidebar', 'unrendered'] = 'sidebar',
    key: str = 'Logout'
)
```

## Changes Made

1. **login()**: Changed from `login("Login", "main")` to `login(location='main', key='Login')`
2. **logout()**: Changed from `logout("Logout", "sidebar")` to `logout(location='sidebar', key='Logout')`

## Valid Location Values

- `'main'` - Display in main area
- `'sidebar'` - Display in sidebar
- `'unrendered'` - Don't render (for custom UI)

