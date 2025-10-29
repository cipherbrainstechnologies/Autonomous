"""
Utility script to generate password hash for streamlit-authenticator
"""

import streamlit_authenticator as stauth
import getpass


def generate_password_hash(password: str = None) -> str:
    """
    Generate password hash for use in secrets.toml.
    
    Args:
        password: Password to hash (if None, will prompt for input)
    
    Returns:
        Hashed password string
    """
    if password is None:
        password = getpass.getpass("Enter password to hash: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return None
    
    # New API: Hasher() with no args, then call hash() method
    hasher = stauth.Hasher()
    hashed = hasher.hash(password)
    
    return hashed


def generate_random_key() -> str:
    """
    Generate random key for cookie authentication.
    
    Returns:
        Random hex string
    """
    import secrets
    return secrets.token_hex(16)


if __name__ == "__main__":
    print("="*50)
    print("Password Hash Generator")
    print("="*50)
    print()
    
    # Generate password hash
    print("Step 1: Generate Password Hash")
    print("-" * 50)
    password_hash = generate_password_hash()
    
    if password_hash:
        print(f"\n✅ Password Hash Generated:")
        print(f"   {password_hash}")
        print("\n📋 Add this to .streamlit/secrets.toml:")
        print(f'   passwords = ["{password_hash}"]')
    
    print("\n" + "="*50)
    print("Step 2: Generate Random Cookie Key")
    print("-" * 50)
    
    cookie_key = generate_random_key()
    print(f"\n✅ Cookie Key Generated:")
    print(f"   {cookie_key}")
    print("\n📋 Add this to .streamlit/secrets.toml:")
    print(f'   key = "{cookie_key}"')
    
    print("\n" + "="*50)
    print("✅ Setup Complete!")
    print("="*50)

