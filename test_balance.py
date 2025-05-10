#!/usr/bin/env python3
"""
Test script to check the Webull account balance and P/L
"""
import os
import sys
import logging
import json
from monitor_pnl_hardened import get_account_balance, get_account_pnl, WebullAuth

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

class Args:
    """Mock args object for the global_args in monitor_pnl_hardened.py"""
    def __init__(self):
        self.test = True
        self.verbose = True
        self.threshold = -300
        self.interval = 60
        self.test_pnl = -250
        self.balance_only = False

def main():
    """Main test function"""
    print("\n=== Webull Account Information Test ===\n")
    
    # Set up mock args for the monitor functions
    import monitor_pnl_hardened
    monitor_pnl_hardened.global_args = Args()
    
    # Get the account balance
    print("Checking account balance...")
    balance = get_account_balance()
    
    if balance is not None:
        print(f"Account Balance: ${balance:.2f}")
    else:
        print("Failed to retrieve account balance.")
        
    # Get the account P/L
    print("\nChecking account P/L...")
    pnl = get_account_pnl()
    
    if pnl is not None:
        print(f"Account P/L: ${pnl:.2f}")
        
        # Calculate percentage if balance is available
        if balance is not None and balance != 0:
            pnl_percent = (pnl / balance) * 100
            print(f"P/L as percentage of balance: {pnl_percent:.2f}%")
    else:
        print("Failed to retrieve account P/L.")
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    main() 