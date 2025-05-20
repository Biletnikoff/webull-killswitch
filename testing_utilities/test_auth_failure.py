#!/usr/bin/env python3
"""
Test script to simulate a 403 authentication error and verify notifications
"""
import os
import sys
import time
import logging
import subprocess
import json

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

def simulate_auth_failure():
    """
    Simulate an authentication failure by modifying the token file
    """
    print("\n=== Simulating Authentication Failure ===\n")
    
    # First ensure log directories exist
    log_dirs = [
        os.path.join(parent_dir, "core_monitoring", "logs"),
        os.path.join(parent_dir, "logs")
    ]
    
    for log_dir in log_dirs:
        os.makedirs(log_dir, exist_ok=True)
        print(f"Created log directory (if it didn't exist): {log_dir}")
    
    # Backup the token file
    token_file = os.path.join(parent_dir, "webull_token.json")
    backup_file = os.path.join(parent_dir, "webull_token.json.bak")
    
    if os.path.exists(token_file):
        print(f"Backing up token file to {backup_file}")
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            # Modify token to force it to be invalid
            if "access_token" in token_data:
                print("Modifying access token to force authentication failure")
                token_data["access_token"] = "invalid_token_to_force_403"
                
                # Write modified token
                with open(token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                    
                print("Token file modified to trigger 403 error")
            else:
                print("Token file does not contain access_token field")
        except Exception as e:
            print(f"Error modifying token file: {e}")
    else:
        print(f"Token file not found: {token_file}")
        return False
    
    # Run the test_balance.py script to trigger an authentication failure
    print("\nRunning test_balance.py to trigger authentication failure...")
    try:
        subprocess.run(["python3", os.path.join(script_dir, "test_balance.py")])
        
        # Wait for log file to be updated
        time.sleep(1)
        
        # Check logs for 403 error
        print("\nChecking logs for 403 errors...")
        found_error = False
        
        for log_dir in log_dirs:
            log_file = os.path.join(log_dir, "monitor_hardened.log")
            if os.path.exists(log_file):
                try:
                    # Check last 20 lines for auth error
                    result = subprocess.run(
                        ["tail", "-n", "20", log_file],
                        capture_output=True,
                        text=True
                    )
                    log_content = result.stdout.strip()
                    
                    if "Token refresh failed with status 403" in log_content or "Authentication failed with status 403" in log_content:
                        print(f"✅ Authentication failure detected in log: {log_file}")
                        found_error = True
                    else:
                        print(f"No recent 403 errors found in: {log_file}")
                except Exception as e:
                    print(f"Error checking log file: {e}")
            else:
                print(f"Log file not found: {log_file}")
        
        if not found_error:
            print("\n❌ No authentication failures detected in logs. Check monitor implementation.")
        
        # Now check if watchdog detects the failure
        print("\nChecking if watchdog detects the auth failure...")
        sys.path.append(os.path.join(parent_dir, "watchdog_components"))
        try:
            from simple_watchdog import check_authentication_status
            
            status = check_authentication_status()
            if status == "expired":
                print("✅ Watchdog correctly detected authentication failure!")
            else:
                print(f"❌ Watchdog failed to detect authentication failure. Status: {status}")
                print("Check the log paths in simple_watchdog.py to make sure they match the actual log locations.")
        except Exception as e:
            print(f"Error importing/running check_authentication_status: {e}")
    finally:
        # Restore original token
        if os.path.exists(backup_file):
            print("\nRestoring original token file")
            try:
                with open(backup_file, 'r') as f:
                    original_data = json.load(f)
                    
                with open(token_file, 'w') as f:
                    json.dump(original_data, f, indent=2)
                    
                print("Original token restored successfully")
            except Exception as e:
                print(f"Error restoring token file: {e}")
                print("You may need to manually restore the token from backup!")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    simulate_auth_failure() 