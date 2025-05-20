#!/usr/bin/env python3
"""
Debug script to test the authentication check function from the watchdog
"""
import os
import sys
import subprocess

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "watchdog_components"))

# Import the function we want to test, but with a modified version for debugging
def debug_check_authentication_status():
    """Debug version of check_authentication_status from simple_watchdog.py"""
    # Get directory paths
    log_paths = [
        os.path.join(parent_dir, "core_monitoring", "logs", "monitor_hardened.log"),
        os.path.join(parent_dir, "logs", "monitor_hardened.log")
    ]
    
    # Search in these log files
    for log_file in log_paths:
        if os.path.exists(log_file):
            print(f"Checking log file: {log_file}")
            
            # Check for auth errors (original approach)
            try:
                result = subprocess.run(
                    ["tail", "-n", "1000", log_file],
                    capture_output=True,
                    text=True
                )
                log_lines = result.stdout.strip()
                
                # Check for known error patterns
                if "Token refresh failed with status 403" in log_lines:
                    print("  FOUND: 'Token refresh failed with status 403'")
                    
                    # Find the actual line with the error
                    line_result = subprocess.run(
                        ["grep", "-n", "Token refresh failed with status 403", log_file],
                        capture_output=True,
                        text=True
                    )
                    print(f"  Last 5 occurrences:")
                    line_nums = line_result.stdout.strip().split('\n')
                    for line in line_nums[-5:]:
                        print(f"    {line}")
                    
                    return "expired"
                elif "Authentication failed with status 403" in log_lines:
                    print("  FOUND: 'Authentication failed with status 403'")
                    
                    # Find the actual line with the error
                    line_result = subprocess.run(
                        ["grep", "-n", "Authentication failed with status 403", log_file],
                        capture_output=True,
                        text=True
                    )
                    print(f"  Last 5 occurrences:")
                    line_nums = line_result.stdout.strip().split('\n')
                    for line in line_nums[-5:]:
                        print(f"    {line}")
                    
                    return "expired"
                else:
                    print("  NO authentication errors found in recent lines")
            except Exception as e:
                print(f"  ERROR checking log file: {e}")
    
    return None

def debug_authentication_check():
    """Debug the authentication status check function"""
    print("\n=== Debugging Authentication Status Check ===\n")
    
    # Log paths that should be checked
    log_paths = [
        os.path.join(parent_dir, "core_monitoring", "logs", "monitor_hardened.log"),
        os.path.join(parent_dir, "logs", "monitor_hardened.log")
    ]
    
    # First, check which log files exist
    print("Checking if log files exist:")
    for log_path in log_paths:
        if os.path.exists(log_path):
            print(f"✅ Found log file: {log_path}")
            
            # Check if the file is readable
            try:
                with open(log_path, 'r') as f:
                    first_line = f.readline().strip()
                    print(f"   First line: {first_line[:80]}")
            except Exception as e:
                print(f"❌ Error reading log file: {e}")
        else:
            print(f"❌ Log file not found: {log_path}")
    
    # Try our debug version of the function
    print("\nRunning debug_check_authentication_status():")
    status = debug_check_authentication_status()
    print(f"Debug status returned: {status}")
    
    # Now run the original function from the watchdog
    print("\nRunning original check_authentication_status():")
    try:
        from simple_watchdog import check_authentication_status
        status = check_authentication_status()
        print(f"Original status returned: {status}")
    except ImportError:
        print("Could not import check_authentication_status")
    
    # If status is None, let's try to debug why
    if status is None:
        print("\nDebugging why status is None:")
        
        # Manually search for 403 errors
        for log_path in log_paths:
            if os.path.exists(log_path):
                print(f"\nSearching '{log_path}' for '403' errors:")
                try:
                    result = subprocess.run(
                        ["grep", "403", log_path], 
                        capture_output=True, 
                        text=True
                    )
                    if result.stdout.strip():
                        print(f"Found 403 errors! First few lines:")
                        lines = result.stdout.strip().split('\n')
                        for i, line in enumerate(lines[:5]):
                            print(f"  {i+1}: {line}")
                        if len(lines) > 5:
                            print(f"  ... and {len(lines) - 5} more lines")
                    else:
                        print("No 403 errors found in this log file.")
                    
                    # Specifically search for the exact pattern
                    print(f"\nSearching for 'Token refresh failed with status 403':")
                    result = subprocess.run(
                        ["grep", "Token refresh failed with status 403", log_path], 
                        capture_output=True, 
                        text=True
                    )
                    if result.stdout.strip():
                        print(f"Found pattern! First few lines:")
                        lines = result.stdout.strip().split('\n')
                        for i, line in enumerate(lines[:5]):
                            print(f"  {i+1}: {line}")
                        if len(lines) > 5:
                            print(f"  ... and {len(lines) - 5} more lines")
                    else:
                        print("Pattern 'Token refresh failed with status 403' NOT found in this log file.")
                        
                    # Search for Authentication failed with status 403
                    print(f"\nSearching for 'Authentication failed with status 403':")
                    result = subprocess.run(
                        ["grep", "Authentication failed with status 403", log_path], 
                        capture_output=True, 
                        text=True
                    )
                    if result.stdout.strip():
                        print(f"Found pattern! First few lines:")
                        lines = result.stdout.strip().split('\n')
                        for i, line in enumerate(lines[:5]):
                            print(f"  {i+1}: {line}")
                        if len(lines) > 5:
                            print(f"  ... and {len(lines) - 5} more lines")
                    else:
                        print("Pattern 'Authentication failed with status 403' NOT found in this log file.")
                    
                except Exception as e:
                    print(f"❌ Error searching log file: {e}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_authentication_check() 