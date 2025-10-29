# Password Hash Error Fix

## Issue
```
string indices must be integers, not 'str' please hash all plain text passwords
```

## Problem

This error occurs when:
1. The password hash in `secrets.toml` is invalid or truncated
2. The library detects the password is not a valid bcrypt hash
3. The library tries to process it as plain text but encounters a format issue

## Solution

### Step 1: Regenerate Password Hash

The hash in your `secrets.toml` appears to be invalid or truncated. Regenerate it:

```powershell
python utils\generate_password_hash.py
```

Enter your password when prompted, then copy the **complete** hash (should be 60 characters).

### Step 2: Verify Hash Format

A valid bcrypt hash should:
- Start with `$2b$12$`
- Be exactly 60 characters long
- Example: `$2b$12$abcdefghijklmnopqrstuvwxyz12345678901234567890123456`

### Step 3: Update secrets.toml

Make sure the hash in `secrets.toml` is:
1. **Complete** - not truncated
2. **In quotes** - `passwords = ["$2b$12$..."]`
3. **Exactly as generated** - no extra spaces or characters

### Step 4: Login

After updating, login with:
- **Username**: `admin`
- **Password**: The **original password** you used when generating the hash

## Common Issues

### Hash Too Short
If hash is less than 60 characters, it's truncated. Regenerate it.

### Hash Validation Failed
The library's `is_hash()` check returns False if:
- Hash format is invalid
- Hash is incomplete
- Hash doesn't start with `$2b$`

### Error About Plain Text
Even with `auto_hash=False`, the library validates hashes. If validation fails, it assumes plain text passwords need hashing.

## Verification

After fixing, check your hash:

```python
import streamlit_authenticator as stauth
hasher = stauth.Hasher()
hash_value = "$2b$12$your_hash_here"
print("Is valid hash?", hasher.is_hash(hash_value))
print("Hash length:", len(hash_value))
```

Both should return:
- `Is valid hash? True`
- `Hash length: 60`

