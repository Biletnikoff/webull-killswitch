#!/usr/bin/env python3
"""
Utility to make a Python script harder to kill by ignoring common termination signals.
Import this into your main script to make it more resistant to being terminated.
"""
import signal
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def make_process_unkillable():
    """Configure the process to ignore common termination signals"""
    try:
        # Ignore SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Ignore SIGTERM (default kill signal)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        # Ignore SIGHUP (terminal closed)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        # Ignore SIGQUIT (Ctrl+\)
        signal.signal(signal.SIGQUIT, signal.SIG_IGN)
        
        # Note: SIGKILL (kill -9) cannot be caught or ignored
        
        logger.info(f"Process {os.getpid()} is now ignoring termination signals")
        return True
    except Exception as e:
        logger.error(f"Failed to set up signal handlers: {e}")
        return False

def setup_log_file(log_path):
    """Set up file logging in addition to console logging"""
    try:
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
            
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to set up log file: {e}")
        return False

def make_unkillable():
    """Alias for backward compatibility"""
    return make_process_unkillable()

if __name__ == "__main__":
    # If run directly, just print information
    print("This is a utility module to make Python processes harder to kill.")
    print("Import this in your main script like this:")
    print("\nfrom installation_maintenance.make_unkillable import make_process_unkillable")
    print("make_process_unkillable()")
    print("\nNote: This will not protect against SIGKILL (kill -9).") 