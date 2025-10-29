# Workaround for Password Hash Error

## The Problem

The `streamlit-authenticator` library has a bug that causes:
```
string indices must be integers, not 'str' please hash all plain text passwords
```

This happens when using `auto_hash=False` with pre-hashed passwords, even though the hash format is correct.

## Solution: Use Plain Text Passwords (Temporary)

Since the library has issues with pre-hashed passwords, use plain text passwords and let the library hash them automatically.

### Step 1: Update secrets.toml

**Change from:**
```toml
[credentials]
names = ["Admin"]
usernames = ["admin"]
passwords = ["$2b$12$xlS7FMHqEL/IO1xcgcNrF.TZhZVz3Aot3J7ZYBa9cZmVoFabCRfoa"]  # Hash
```

**To:**
```toml
[credentials]
names = ["Admin"]
usernames = ["admin"]
passwords = ["your_actual_password_here"]  # Plain text - library will hash it
```

**Example:**
```toml
[credentials]
names = ["Admin"]
usernames = ["admin"]
passwords = ["Admin123!"]
```

### Step 2: The Code Will Auto-Detect

The updated code will:
- Detect if passwords are hashed (`$2b$` prefix) or plain text
- Use `auto_hash=True` for plain text passwords
- Use `auto_hash=False` for hashed passwords (though this has the bug)

### Step 3: Login

Use the same credentials:
- **Username**: `admin`
- **Password**: `Admin123!` (or whatever plain text password you put in secrets.toml)

## Security Note

⚠️ **For production**, you'd want:
1. Keep passwords hashed in secrets.toml
2. Fix the library bug or use a different authentication method
3. Use environment variables instead of secrets.toml for production

For **development/testing**, using plain text in secrets.toml is acceptable if the file is git-ignored.

## Why This Works

The library's `auto_hash=True` mode works correctly - it hashes passwords internally during login validation. The bug only affects `auto_hash=False` when validating pre-hashed passwords.

## Alternative: Use Different Auth Library

If this continues to cause issues, consider:
- Using Streamlit's built-in secrets management differently
- Implementing custom authentication using bcrypt directly
- Using a different authentication library

