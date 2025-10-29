# Setup Login Credentials - Quick Guide

## Current Configuration

Based on your `secrets.toml`, you have:
- **Username**: `admin`
- **Password Hash**: Still needs to be generated (currently placeholder)
- **Cookie Key**: Still needs to be generated (currently placeholder)

## Step 1: Generate Password Hash & Cookie Key

Run the utility script:

```powershell
python utils/generate_password_hash.py
```

This will:
1. Ask you to enter a password (twice for confirmation)
2. Generate a password hash
3. Generate a random cookie key
4. Show you what to add to `secrets.toml`

**Example Output:**
```
Step 1: Generate Password Hash
Enter password to hash: ****
Confirm password: ****

✅ Password Hash Generated:
   $2b$12$abcdefghijklmnopqrstuvwxyz1234567890

Step 2: Generate Random Cookie Key
✅ Cookie Key Generated:
   1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p

✅ Setup Complete!
```

## Step 2: Update secrets.toml

Edit `.streamlit/secrets.toml` and replace:

```toml
[credentials]
names = ["Admin"]
usernames = ["admin"]
passwords = ["$2b$12$REPLACE_WITH_YOUR_HASHED_PASSWORD"]  # Replace this

[cookie]
name = "nifty_auth"
key = "REPLACE_WITH_RANDOM_KEY"  # Replace this
expiry_days = 30
```

**With your generated values:**

```toml
[credentials]
names = ["Admin"]
usernames = ["admin"]
passwords = ["$2b$12$YOUR_GENERATED_HASH_HERE"]  # Paste hash from Step 1

[cookie]
name = "nifty_auth"
key = "YOUR_GENERATED_KEY_HERE"  # Paste key from Step 1
expiry_days = 30
```

## Step 3: Login Credentials

After updating `secrets.toml`, use these credentials to log in:

- **Username**: `admin`
- **Password**: The **ORIGINAL password** you entered when generating the hash (NOT the hash itself!)

### Important Notes:

1. ✅ You use the **ORIGINAL password** at login (e.g., "mypassword123")
2. ❌ You do NOT use the hash in the login form
3. ✅ The hash goes in `secrets.toml`
4. ✅ The original password goes in the login form

## Quick Setup Example

Let's say you want password: `Admin123!`

1. Run:
   ```powershell
   python utils/generate_password_hash.py
   ```
   Enter: `Admin123!` (twice)

2. Copy the generated hash to `secrets.toml`

3. Login with:
   - Username: `admin`
   - Password: `Admin123!`

## Verify Setup

After updating `secrets.toml`, verify:

```powershell
python verify_setup.py
```

This should show:
- ✅ secrets.toml: [credentials] section found
- ✅ secrets.toml: [cookie] section found  
- ✅ secrets.toml: [broker] section found
- ⚠️ secrets.toml: Contains placeholder values - Update with real credentials

After you update, it should show all ✅ for secrets.

## Troubleshooting

### "Invalid credentials"
- Make sure you're using the **original password** (not the hash)
- Verify the hash in `secrets.toml` matches what was generated
- Check username is exactly `admin` (case-sensitive)

### "Authentication setup failed"
- Verify `secrets.toml` has no placeholder values
- Make sure hash and key were properly generated
- Check file encoding is UTF-8

