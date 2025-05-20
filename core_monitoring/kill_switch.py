#!/usr/bin/env python3
"""
Kill Switch Core Logic
Handles the core logic for triggering kill actions and notifications
"""
import os
import sys
import subprocess
import logging

# Add parent directory to path to allow imports from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import from other modules using relative imports
from installation_maintenance.make_unkillable import make_process_unkillable

# Configure logging
logger = logging.getLogger(__name__)

def execute_kill_switch(pnl_value=None, balance=None):
    """Execute the kill switch action to close Webull"""
    try:
        logger.info("EXECUTING KILL SWITCH")
        
        # Get the path to the AppleScript
        applescript_dir = os.path.join(parent_dir, "applescripts")
        kill_script = os.path.join(applescript_dir, "killTradingApp.scpt")
        
        if not os.path.exists(kill_script):
            logger.error(f"Kill script not found at {kill_script}")
            return False
        
        # Execute the script
        logger.info(f"Executing kill script: {kill_script}")
        result = subprocess.run(
            ["osascript", kill_script],
            check=False,
            capture_output=True,
            text=True
        )
        
        # Log the result
        if result.returncode == 0:
            logger.info("Kill switch executed successfully")
            return True
        else:
            logger.error(f"Kill switch failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error executing kill switch: {e}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test the kill switch
    execute_kill_switch()
