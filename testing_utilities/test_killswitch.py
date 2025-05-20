#!/usr/bin/env python3
"""
Test script for kill switch functionality
"""
import os
import time
import subprocess
import logging
from dotenv import load_dotenv
import sys

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Try to import from core_monitoring
try:
    from core_monitoring.kill_switch import execute_kill_switch
    DIRECT_IMPORT = True
except ImportError:
    DIRECT_IMPORT = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Helper function to parse env values and strip comments
def get_env_value(key, default, convert_func=str):
    value = os.getenv(key, default)
    if '#' in value:
        value = value.split('#')[0].strip()
    try:
        return convert_func(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing {key}: {e}, using default: {default}")
        return convert_func(default)

# Configuration
THRESHOLD = get_env_value('PNL_THRESHOLD', '-500', float)
THRESHOLD_TYPE = get_env_value('THRESHOLD_TYPE', 'DOLLAR', str).upper()
CHECK_INTERVAL = get_env_value('CHECK_INTERVAL', '60', int)

# Find the kill script in the new directory structure
SCRIPT_PATH = os.path.join(parent_dir, 'applescripts', 'killTradingApp.scpt')

# Ensure the kill script exists
if not os.path.exists(SCRIPT_PATH):
    # Try alternative locations
    alternative_paths = [
        os.path.join(parent_dir, 'killTradingApp.scpt'),  # Root directory (old location)
        os.path.join(script_dir, 'killTradingApp.scpt'),  # In the testing directory
    ]
    
    for path in alternative_paths:
        if os.path.exists(path):
            SCRIPT_PATH = path
            break
    else:
        raise FileNotFoundError(f"Kill script not found at {SCRIPT_PATH} or alternative locations")

logger.info(f"Using kill script at: {SCRIPT_PATH}")

def trigger_kill():
    """Execute the kill switch to close Webull"""
    try:
        if DIRECT_IMPORT:
            # Use the imported function if available
            logger.info("Using direct import of execute_kill_switch")
            result = execute_kill_switch(-1000.0, 10000.0)  # Pass test values
            if result:
                logger.info("Kill switch executed successfully via direct import")
                return True
            else:
                logger.error("Kill switch execution failed via direct import")
                return False
        else:
            # Fall back to direct AppleScript execution
            logger.info(f"Executing kill script directly: {SCRIPT_PATH}")
            result = subprocess.run(['osascript', SCRIPT_PATH], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Kill script executed: {result.stdout}")
            return True
    except Exception as e:
        logger.error(f"Error executing kill script: {e}")
        return False

def simulate_pnl_decline():
    """Simulate a declining P/L until threshold is reached"""
    # Starting values
    initial_investment = 10000.0  # $10,000 initial investment
    current_value = initial_investment
    step = 100.0  # Decrease by $100 each iteration
    
    threshold_type_str = "Dollar" if THRESHOLD_TYPE == 'DOLLAR' else "Percentage"
    threshold_display = f"${THRESHOLD:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{THRESHOLD:.2%}"
    
    logger.info(f"Starting P/L simulation with {threshold_type_str} threshold: {threshold_display}")
    logger.info(f"Initial investment: ${initial_investment:.2f}")
    
    # Simulation loop
    while True:
        # Decrease value (simulating losing trades)
        current_value -= step
        
        # Calculate P/L metrics
        dollar_pnl = current_value - initial_investment
        pct_pnl = dollar_pnl / initial_investment
        
        logger.info(f"Current value: ${current_value:.2f}")
        logger.info(f"Current P/L: ${dollar_pnl:.2f} ({pct_pnl:.2%})")
        
        # Check if threshold is reached
        threshold_reached = False
        if THRESHOLD_TYPE == 'DOLLAR':
            threshold_reached = dollar_pnl <= THRESHOLD
        else:
            threshold_reached = pct_pnl <= THRESHOLD
        
        if threshold_reached:
            threshold_display = f"${THRESHOLD:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{THRESHOLD:.2%}"
            current_display = f"${dollar_pnl:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{pct_pnl:.2%}"
            
            logger.warning(f"P/L threshold reached: {current_display} <= {threshold_display}")
            if trigger_kill():
                logger.info("Kill switch activated successfully")
                break
            else:
                logger.error("Failed to activate kill switch")
                break
        
        # Brief pause between iterations
        time.sleep(1)

if __name__ == "__main__":
    try:
        simulate_pnl_decline()
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise 