#!/usr/bin/env python3
"""
Production Watchdog for Webull Kill Switch
Starts the monitor script in production mode
"""
import os
import sys
import subprocess
import time

def load_env_config():
    """Load configuration from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_vars = {}
    
    if os.path.exists(env_file):
        print("Loading configuration from .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
                    except ValueError:
                        continue
        return env_vars
    else:
        print(".env file not found, using defaults")
        return {}

def main():
    # Directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to monitor script
    monitor_script = os.path.join(script_dir, "monitor_pnl_hardened.py")
    
    # Get command line arguments
    args = sys.argv[1:]
    
    # Load configuration from .env file
    env_config = load_env_config()
    
    # Ensure threshold is set (from .env or default)
    if not any(arg.startswith("--threshold") for arg in args):
        threshold = env_config.get('DEFAULT_THRESHOLD', '-300')
        args.append(f"--threshold={threshold}")
    
    # Build the command
    cmd = ["python3", monitor_script] + args
    print(f"Starting production monitor with command: {' '.join(cmd)}")
    
    # Start the monitor script
    try:
        process = subprocess.Popen(cmd)
        print(f"Production monitor started with PID: {process.pid}")
        print("Monitor is running in PRODUCTION mode - will only operate during market hours")
        
        # Keep script running to maintain the shell session
        try:
            while True:
                time.sleep(10)
                # Check if process is still running
                if process.poll() is not None:
                    print("Monitor process has stopped, restarting...")
                    process = subprocess.Popen(cmd)
                    print(f"Restarted production monitor with PID: {process.pid}")
        except KeyboardInterrupt:
            print("Exiting watchdog due to keyboard interrupt")
            
    except Exception as e:
        print(f"Error starting monitor: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 