#!/usr/bin/env python3
"""
Test script to verify the new directory structure and imports work correctly
"""
import os
import sys
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Test imports from each directory
def test_imports():
    logger.info("Testing imports from each directory...")
    
    # Core Monitoring
    try:
        from core_monitoring.kill_switch import execute_kill_switch
        logger.info("✅ Successfully imported from core_monitoring")
    except ImportError as e:
        logger.error(f"❌ Failed to import from core_monitoring: {e}")
        return False
    
    # Authentication
    try:
        from authentication.webull_auth import WebullAuth
        logger.info("✅ Successfully imported from authentication")
    except ImportError as e:
        logger.error(f"❌ Failed to import from authentication: {e}")
        return False
    
    # Installation Maintenance
    try:
        from installation_maintenance.make_unkillable import make_process_unkillable
        logger.info("✅ Successfully imported from installation_maintenance")
    except ImportError as e:
        logger.error(f"❌ Failed to import from installation_maintenance: {e}")
        return False
    
    # System Tools (if applicable)
    try:
        import system_tools.check_status
        logger.info("✅ Successfully imported from system_tools")
    except ImportError as e:
        logger.error(f"❌ Failed to import from system_tools: {e}")
    
    # Watchdog Components
    try:
        import watchdog_components.simple_watchdog
        logger.info("✅ Successfully imported from watchdog_components")
    except ImportError as e:
        logger.error(f"❌ Failed to import from watchdog_components: {e}")
        return False
    
    return True

# Test file paths
def test_file_paths():
    logger.info("Testing file paths...")
    
    # Check key file paths
    files_to_check = [
        os.path.join(parent_dir, "core_monitoring", "monitor_pnl_hardened.py"),
        os.path.join(parent_dir, "applescripts", "killTradingApp.scpt"),
        os.path.join(parent_dir, "authentication", "webull_auth.py"),
        os.path.join(parent_dir, "webull_token.json"),  # This is still in the root
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            logger.info(f"✅ Found {os.path.basename(file_path)}")
        else:
            logger.error(f"❌ Missing {file_path}")
            all_exist = False
    
    return all_exist

def main():
    logger.info("=== Testing New Directory Structure ===")
    
    # Test imports
    import_result = test_imports()
    if import_result:
        logger.info("✅ All imports successful")
    else:
        logger.error("❌ Some imports failed")
    
    # Test file paths
    path_result = test_file_paths()
    if path_result:
        logger.info("✅ All file paths valid")
    else:
        logger.error("❌ Some file paths are invalid")
    
    # Overall result
    if import_result and path_result:
        logger.info("🎉 New directory structure is working correctly!")
        return 0
    else:
        logger.error("❌ New directory structure has issues that need to be fixed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 