#!/usr/bin/env python3
"""
Simplified Webull Monitor Test Script
This script shows the monitoring logic with visible output and no watchdog.
"""
import os
import sys
import subprocess
import time
import logging
from datetime import datetime

# Configuration
PNL_THRESHOLD = -500.0  # Trigger kill switch when P/L drops below this value
CHECK_INTERVAL = 5      # Check P/L every this many seconds

# Configure logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def print_status_update(cycle_count, current_pnl=None):
    """Print a visible status update to the console"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_line = f"[{now}] Kill Switch Monitor Active - Cycle: {cycle_count}"
    
    if current_pnl is not None:
        status_line += f" | Current P/L: ${current_pnl:.2f}"
        
    # Calculate threshold percentage
    pct = (current_pnl / 10000.0) * 100 if current_pnl is not None else 0
    status_line += f" | Threshold: ${PNL_THRESHOLD:.2f} | P/L%: {pct:.2f}%"
    
    # Add some visual indicator of status
    if current_pnl is not None and current_pnl <= PNL_THRESHOLD:
        status_line += " | STATUS: ⚠️ THRESHOLD REACHED ⚠️"
    else:
        status_line += " | STATUS: ✅ Normal"
    
    print(status_line)
    sys.stdout.flush()

def simulate_get_pnl(cycle):
    """
    Simulate getting P/L from Webull API
    This follows a pattern to trigger the kill switch at certain cycles
    """
    # Create a deterministic pattern based on cycle
    cycle_mod = cycle % 5  # 0-4 based on the cycle
    
    if cycle_mod == 0:
        return -100.0
    elif cycle_mod == 1:
        return -300.0
    elif cycle_mod == 2:
        return -400.0
    elif cycle_mod == 3:
        return -550.0  # This should trigger the kill switch
    else:
        return -600.0

def execute_kill_switch():
    """Simulate executing the kill switch script"""
    print("\n" + "!"*80)
    print("KILL SWITCH ACTIVATED - P/L THRESHOLD REACHED")
    print("!"*80)
    print("\nExecuting kill script...")
    print("Kill script activated - would close Webull applications in real operation")
    print("Kill switch activation complete\n")
    return True

def main():
    """Main monitoring function"""
    print("\n" + "="*80)
    print("   WEBULL KILL SWITCH MONITOR TEST   ".center(80, '*'))
    print("="*80 + "\n")
    
    print(f"Starting monitor test with:")
    print(f"- P/L threshold: ${PNL_THRESHOLD:.2f}")
    print(f"- Check interval: {CHECK_INTERVAL} seconds")
    print(f"- This test will show visible output without any watchdog features")
    print(f"- Press Ctrl+C to exit the test")
    print()
    
    # Initialize cycle counter
    cycle_count = 0
    
    # Main monitoring loop
    try:
        while True:
            cycle_count += 1
            
            print("\n" + "-"*40)
            print(f"Cycle {cycle_count} - Checking P/L...")
            
            # Get the current P/L
            current_pnl = simulate_get_pnl(cycle_count)
            
            # Log the current P/L
            logger.info(f"Current P/L: ${current_pnl:.2f}")
            
            # Print a status update with P/L
            print_status_update(cycle_count, current_pnl)
            
            # Check if P/L is below threshold
            if current_pnl <= PNL_THRESHOLD:
                logger.warning(f"P/L threshold reached: ${current_pnl:.2f} <= ${PNL_THRESHOLD:.2f}")
                
                # Execute kill switch
                execute_kill_switch()
                
                # Take a short break after triggering the kill switch
                print("Taking a short break after kill switch activation...")
                time.sleep(3)  # 3 seconds for testing
            
            # Wait for the next check
            print(f"Waiting {CHECK_INTERVAL} seconds before next check...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nMonitor test interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main() 