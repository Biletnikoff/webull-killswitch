#!/usr/bin/env python3
"""
Status checker for Webull Kill Switch

This script checks the status of the Webull Kill Switch monitoring system
and provides feedback on its operational state.
"""
import os
import sys
import subprocess
import time
from datetime import datetime

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# If this is in system_tools, we need to go up one directory
if os.path.basename(SCRIPT_DIR) == "system_tools":
    SCRIPT_DIR = os.path.dirname(SCRIPT_DIR)
MONITOR_SCRIPT = "monitor_pnl_hardened.py"
WATCHDOG_SCRIPT_NAMES = ["watchdog.py", "simple_watchdog.py", "production_watchdog.py"]
LAUNCHD_PLIST = "com.webull.killswitch.plist"
WATCHDOG_DIR = os.path.join(SCRIPT_DIR, "watchdog_components")
LOG_FILE = os.path.join(SCRIPT_DIR, "logs", "monitor_hardened.log")
WATCHDOG_FILE = os.path.join(WATCHDOG_DIR, "simple_watchdog.py")
LAUNCHD_PATH = os.path.expanduser("~/Library/LaunchAgents/" + LAUNCHD_PLIST)
LOCAL_PLIST_PATH = os.path.join(SCRIPT_DIR, LAUNCHD_PLIST)

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header():
    """Print the header for the status report"""
    print("=" * 80)
    print("*********************   WEBULL KILL SWITCH STATUS CHECKER   *********************".center(80))
    print("=" * 80)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Check running from: {__file__}\n")

def run_command(cmd):
    """Run a command and return the output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return f"Error: {str(e)}", 1

def check_process_running(process_name):
    """Check if a process is running by name"""
    output, exit_code = run_command(["pgrep", "-f", process_name])
    if exit_code == 0 and output:
        return output.strip().split("\n")
    return []

def check_monitor_process():
    """Check if the monitor process is running"""
    print("\n1. Checking kill switch monitoring process...")
    pids = check_process_running(MONITOR_SCRIPT)
    
    if pids:
        print(f"{GREEN}✅ Kill switch monitoring process is RUNNING{RESET}")
        for pid in pids:
            print(f"   Process ID: {pid}")
            
            # Get command details
            cmd_details, _ = run_command(["ps", "-p", pid, "-o", "command"])
            if cmd_details:
                details = cmd_details.split('\n')
                detail_text = details[1] if len(details) > 1 else ''
                print(f"   Details: {detail_text}")
        return True
    else:
        print(f"{RED}❌ Kill switch monitoring process is NOT RUNNING{RESET}")
        return False

def check_watchdog_process():
    """Check if the watchdog process is running"""
    print("\n2. Checking watchdog process...")
    
    # Check for both watchdog scripts
    pids = []
    for watchdog_name in WATCHDOG_SCRIPT_NAMES:
        pids.extend(check_process_running(watchdog_name))
    
    if pids:
        print(f"{GREEN}✅ Watchdog process is RUNNING{RESET}")
        for pid in pids:
            print(f"   Process ID: {pid}")
            
            # Get command details
            cmd_details, _ = run_command(["ps", "-p", pid, "-o", "command"])
            if cmd_details:
                details = cmd_details.split('\n')
                detail_text = details[1] if len(details) > 1 else ''
                print(f"   Details: {detail_text}")
        return True
    else:
        print(f"{RED}❌ Watchdog process is NOT RUNNING{RESET}")
        return False

def check_launch_agent():
    """Check if the launch agent is loaded"""
    print("\n3. Checking launchd service status...")
    
    # Check if plist exists in LaunchAgents directory
    if not os.path.exists(LAUNCHD_PATH):
        print(f"{RED}❌ Launch agent is NOT INSTALLED{RESET}")
        return False
    
    # Check if launch agent is loaded
    output, exit_code = run_command(["launchctl", "list"])
    if "com.webull.killswitch" in output:
        print(f"{GREEN}✅ Launch agent is LOADED{RESET}")
        return True
    else:
        print(f"{YELLOW}⚠️ Launch agent is INSTALLED but NOT LOADED{RESET}")
        return False

def check_log_file():
    """Check if the log file exists and show last lines"""
    print("\n4. Checking log file...")
    if os.path.exists(LOG_FILE):
        print(f"{GREEN}✅ Log file exists{RESET}")
        
        # Show last 10 lines
        output, _ = run_command(["tail", "-n", "10", LOG_FILE])
        print("   Last 10 lines:")
        for line in output.split("\n"):
            print(f"     {line}")
        return True
    else:
        print(f"{RED}❌ Log file not found{RESET}")
        return False

def check_watchdog_file():
    """Check if the watchdog file exists"""
    print("\n5. Checking watchdog file...")
    
    # Check for any watchdog script
    watchdog_exists = False
    found_watchdogs = []
    
    # First check in watchdog_components directory
    watchdog_dir = os.path.join(SCRIPT_DIR, "watchdog_components")
    for watchdog_name in WATCHDOG_SCRIPT_NAMES:
        watchdog_path = os.path.join(watchdog_dir, watchdog_name)
        if os.path.exists(watchdog_path):
            print(f"{GREEN}✅ Watchdog file exists: watchdog_components/{watchdog_name}{RESET}")
            
            # Check if file is executable
            if os.access(watchdog_path, os.X_OK):
                print(f"{GREEN}✅ Watchdog file is executable{RESET}")
            else:
                print(f"{YELLOW}⚠️ Watchdog file is not executable{RESET}")
            
            watchdog_exists = True
            found_watchdogs.append(watchdog_name)
    
    # For backward compatibility, also check in root directory
    for watchdog_name in WATCHDOG_SCRIPT_NAMES:
        watchdog_path = os.path.join(SCRIPT_DIR, watchdog_name)
        if os.path.exists(watchdog_path) and watchdog_name not in found_watchdogs:
            print(f"{YELLOW}⚠️ Found legacy watchdog file in root directory: {watchdog_name}{RESET}")
            print(f"{YELLOW}⚠️ Consider moving it to the watchdog_components directory{RESET}")
            
            # Check if file is executable
            if os.access(watchdog_path, os.X_OK):
                print(f"{GREEN}✅ Watchdog file is executable{RESET}")
            else:
                print(f"{YELLOW}⚠️ Watchdog file is not executable{RESET}")
            
            watchdog_exists = True
            found_watchdogs.append(watchdog_name)
    
    if not watchdog_exists:
        print(f"{RED}❌ Watchdog file does not exist{RESET}")
        return False
    
    return True

def print_summary(monitor_status, watchdog_status, launch_agent_status, log_file_status, watchdog_file_status):
    """Print summary of status checks"""
    print("\n" + "=" * 40)
    print(f"{BOLD}SUMMARY:{RESET}")
    print("=" * 40)
    print(f"Monitor Process: {GREEN}✅ Running{RESET}" if monitor_status else f"Monitor Process: {RED}❌ Not Running{RESET}")
    print(f"Watchdog Process: {GREEN}✅ Running{RESET}" if watchdog_status else f"Watchdog Process: {RED}❌ Not Running{RESET}")
    print(f"Launch Agent: {GREEN}✅ Loaded{RESET}" if launch_agent_status else f"Launch Agent: {YELLOW}⚠️ Not Loaded{RESET}")
    print(f"Log File: {GREEN}✅ Exists{RESET}" if log_file_status else f"Log File: {RED}❌ Not Found{RESET}")
    print(f"Watchdog File: {GREEN}✅ Valid{RESET}" if watchdog_file_status else f"Watchdog File: {RED}❌ Invalid{RESET}")
    
    print("\nRecommended actions:")
    if not monitor_status and not watchdog_status:
        print(f"- Start the monitor process: {BOLD}python3 watchdog_components/respawn_monitor.py --test{RESET}")
    elif not monitor_status:
        print(f"- Monitor not running. Start it with: {BOLD}python3 core_monitoring/monitor_pnl_hardened.py --test{RESET}")
    elif not watchdog_status:
        print(f"- Watchdog not running. Start it with: {BOLD}python3 watchdog_components/respawn_monitor.py --test{RESET}")
    elif not watchdog_file_status:
        using_alternate = False
        for name in WATCHDOG_SCRIPT_NAMES:
            if name != "watchdog.py" and any(check_process_running(name)):
                using_alternate = True
                print(f"- Using {name} instead of standard watchdog.py (this is OK)")
                break
        
        if not using_alternate:
            print(f"- Watchdog file is invalid. Run: {BOLD}python3 watchdog_components/respawn_monitor.py --test{RESET}")
    else:
        print(f"- All systems operational! No action needed.")

def main():
    """Main function"""
    print_header()
    
    # Run checks
    monitor_status = check_monitor_process()
    watchdog_status = check_watchdog_process()
    launch_agent_status = check_launch_agent()
    log_file_status = check_log_file()
    watchdog_file_status = check_watchdog_file()
    
    # Print summary
    print_summary(monitor_status, watchdog_status, launch_agent_status, log_file_status, watchdog_file_status)
    
    print("\nDone!")
    
    # Return status code
    if monitor_status and watchdog_status:
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main()) 