#!/usr/bin/env python3
"""
Test script to verify auth failure notifications are working properly
"""
import os
import sys
import time
import logging
import subprocess

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

def test_monitor_auth_notification():
    """
    Test that the monitor sends a notification when authentication fails
    """
    print("\n=== Testing Authentication Failure Notifications ===\n")
    
    # First make sure we are using paths to the proper log locations
    log_dirs = [
        os.path.join(parent_dir, "core_monitoring", "logs"),
        os.path.join(parent_dir, "logs")
    ]
    
    for log_dir in log_dirs:
        os.makedirs(log_dir, exist_ok=True)
        print(f"Created log directory (if it didn't exist): {log_dir}")
    
    # Run the test_balance.py script to force an authentication failure
    print("Running test_balance.py to generate an authentication failure...")
    subprocess.run(["python3", os.path.join(script_dir, "test_balance.py")])
    
    # Wait a moment for log files to be written
    time.sleep(1)
    
    # Check if watchdog has detected the authentication failure
    print("\nChecking if watchdog detects the authentication failure...")
    
    # Import the check function from the watchdog
    sys.path.append(os.path.join(parent_dir, "watchdog_components"))
    try:
        from simple_watchdog import check_authentication_status
        
        status = check_authentication_status()
        print(f"Authentication status detected by watchdog: {status}")
        
        if status == "expired":
            print("✅ SUCCESS: Watchdog correctly detected authentication failure!")
        else:
            print("❌ FAILURE: Watchdog did not detect authentication failure.")
            print("Check the log paths in simple_watchdog.py and make sure they match the actual log locations.")
    except ImportError:
        print("❌ FAILURE: Could not import check_authentication_status from simple_watchdog.py")
    
    # Check the actual log files
    print("\nSearching for 403 errors in log files...")
    
    for log_dir in log_dirs:
        monitor_log = os.path.join(log_dir, "monitor_hardened.log")
        if os.path.exists(monitor_log):
            print(f"Checking log file: {monitor_log}")
            
            # Check for 403 error patterns
            try:
                result = subprocess.run(
                    ["grep", "403", monitor_log],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    print(f"Found 403 errors in log file:")
                    lines = result.stdout.strip().split('\n')
                    for line in lines[:3]:  # First 3 lines
                        print(f"  {line}")
                    if len(lines) > 3:
                        print(f"  ... and {len(lines) - 3} more lines")
                else:
                    print("No 403 errors found in log file")
            except Exception as e:
                print(f"Error searching log file: {e}")
        else:
            print(f"Log file not found: {monitor_log}")
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    test_monitor_auth_notification() 