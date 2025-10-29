"""
Setup Verification Script
Verifies that all components are properly configured for local run
"""

import os
import sys
from pathlib import Path

# Ensure we're in the project root directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        # Set console to UTF-8 encoding
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        # Fallback: Use ASCII-safe characters
        pass

try:
    import yaml
except ImportError:
    print("[WARNING] PyYAML not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml

# Use ASCII-safe characters for Windows compatibility
CHECK_MARK = "[OK]" if sys.platform == 'win32' else "✅"
CROSS_MARK = "[FAIL]" if sys.platform == 'win32' else "❌"
WARN_MARK = "[WARN]" if sys.platform == 'win32' else "⚠️"

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"{CHECK_MARK} Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"{CROSS_MARK} Python version {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'streamlit_authenticator',
        'pandas',
        'numpy',
        'yaml'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'yaml':
                __import__('yaml')
            else:
                __import__(package.replace('_', '-'))
            print(f"{CHECK_MARK} {package}")
        except ImportError:
            print(f"{CROSS_MARK} {package} - Not installed")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        'engine',
        'dashboard',
        'config',
        'data/historical',
        '.streamlit',
        'logs',
        'memory-bank',
        'utils'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"{CHECK_MARK} Directory: {directory}")
        else:
            print(f"{CROSS_MARK} Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def check_files():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'config/config.yaml',
        'engine/strategy_engine.py',
        'engine/signal_handler.py',
        'engine/trade_logger.py',
        'engine/broker_connector.py',
        'engine/backtest_engine.py',
        'dashboard/ui_frontend.py',
        'utils/generate_password_hash.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"{CHECK_MARK} File: {file_path}")
        else:
            print(f"{CROSS_MARK} File missing: {file_path}")
            all_exist = False
    
    return all_exist

def check_secrets():
    """Check if secrets.toml exists and is configured"""
    secrets_path = Path('.streamlit/secrets.toml')
    
    if not secrets_path.exists():
        print(f"{WARN_MARK} secrets.toml not found - You'll need to create it")
        print("   Run: python utils/generate_password_hash.py")
        return False
    
    try:
        with open(secrets_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic checks
        checks_passed = 0
        if '[credentials]' in content:
            checks_passed += 1
            print(f"{CHECK_MARK} secrets.toml: [credentials] section found")
        else:
            print(f"{CROSS_MARK} secrets.toml: [credentials] section missing")
        
        if '[cookie]' in content:
            checks_passed += 1
            print(f"{CHECK_MARK} secrets.toml: [cookie] section found")
        else:
            print(f"{CROSS_MARK} secrets.toml: [cookie] section missing")
        
        if '[broker]' in content:
            checks_passed += 1
            print(f"{CHECK_MARK} secrets.toml: [broker] section found")
        else:
            print(f"{CROSS_MARK} secrets.toml: [broker] section missing")
        
        # Check for placeholder values
        if 'YOUR_' in content or 'REPLACE_' in content:
            print(f"{WARN_MARK} secrets.toml: Contains placeholder values - Update with real credentials")
            return False
        
        return checks_passed == 3
    except Exception as e:
        print(f"{CROSS_MARK} Error reading secrets.toml: {e}")
        return False

def check_config():
    """Check if config.yaml is valid"""
    config_path = Path('config/config.yaml')
    
    if not config_path.exists():
        print("❌ config.yaml not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_keys = ['lot_size', 'strategy']
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"{CROSS_MARK} config.yaml: Missing keys: {missing_keys}")
            return False
        
        print(f"{CHECK_MARK} config.yaml: Valid configuration")
        return True
    except Exception as e:
        print(f"{CROSS_MARK} Error reading config.yaml: {e}")
        return False

def check_logs():
    """Check if logs directory and files are set up"""
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print("⚠️  logs/ directory not found - Will be created on first run")
        return True
    
    trades_csv = logs_dir / 'trades.csv'
    if trades_csv.exists():
        print(f"{CHECK_MARK} logs/trades.csv exists")
    else:
        print(f"{WARN_MARK} logs/trades.csv not found - Will be created on first run")
    
    errors_log = logs_dir / 'errors.log'
    if errors_log.exists():
        print(f"{CHECK_MARK} logs/errors.log exists")
    else:
        print(f"{WARN_MARK} logs/errors.log not found - Will be created on first run")
    
    return True

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("NIFTY Options Trading System - Setup Verification")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Checking Python version...")
    results.append(("Python Version", check_python_version()))
    print()
    
    print("2. Checking dependencies...")
    deps_ok, missing = check_dependencies()
    results.append(("Dependencies", deps_ok))
    if missing:
        print(f"   Install missing packages: pip install {' '.join(missing)}")
    print()
    
    print("3. Checking directories...")
    results.append(("Directories", check_directories()))
    print()
    
    print("4. Checking files...")
    results.append(("Files", check_files()))
    print()
    
    print("5. Checking configuration...")
    results.append(("Config", check_config()))
    print()
    
    print("6. Checking secrets...")
    results.append(("Secrets", check_secrets()))
    print()
    
    print("7. Checking logs...")
    results.append(("Logs", check_logs()))
    print()
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = f"{CHECK_MARK} PASS" if passed else f"{CROSS_MARK} FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print(f"{CHECK_MARK} All checks passed! System is ready to run.")
        print()
        print("Next steps:")
        print("  1. Run: python -m streamlit run dashboard/ui_frontend.py")
        print("  2. Or use: .\\run_local.ps1 (PowerShell) or .\\run_local.bat (CMD)")
        print("  3. Or use: ./run_local.sh (Linux/Mac)")
        return 0
    else:
        print(f"{WARN_MARK} Some checks failed. Please fix the issues above before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

