#!/usr/bin/env python3
"""
Super Simple Webull Monitor Test
Just demonstrates the basic monitoring logic without any complex features
"""
import time
import random
from datetime import datetime

# Configuration
PNL_THRESHOLD = -500.0
CHECK_INTERVAL = 2  # seconds

def main():
    """Simple monitoring loop"""
    print("\n=== WEBULL KILL SWITCH SIMPLE TEST ===\n")
    print(f"P/L Threshold: ${PNL_THRESHOLD}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print("Press Ctrl+C to exit\n")
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            
            # Get timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Generate P/L value (starts at -100 and gradually decreases)
            if cycle <= 5:
                pnl = -100 * cycle
            else:
                # After cycle 5, vary between -450 and -550
                pnl = -450 - random.randint(0, 100)
            
            # Print status
            status = "⚠️ THRESHOLD REACHED" if pnl <= PNL_THRESHOLD else "✅ OK"
            print(f"[{timestamp}] Cycle {cycle:2d} | P/L: ${pnl:.2f} | Status: {status}")
            
            # Check threshold
            if pnl <= PNL_THRESHOLD:
                print(f"\n!!! KILL SWITCH ACTIVATED - P/L ${pnl:.2f} reached threshold ${PNL_THRESHOLD:.2f} !!!\n")
            
            # Wait for next check
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nTest terminated by user")

if __name__ == "__main__":
    main() 