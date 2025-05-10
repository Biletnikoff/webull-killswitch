#!/usr/bin/env python3
import sys
import traceback

try:
    # Import webull package
    print("Importing webull package...")
    from webull import webull
    print("Webull package imported successfully.")
    
    # Create instance
    print("Creating Webull instance...")
    wb = webull()
    print("Webull instance created.")
    
    # Try to get market status (doesn't require authentication)
    print("Getting market status...")
    status = wb.get_market_status()
    print(f"Market status: {status}")
    
    # Try to get quote for a symbol
    print("Getting quote for AAPL...")
    quote = wb.get_quote("AAPL")
    if quote:
        print(f"AAPL current price: ${quote.get('close', 'N/A')}")
    else:
        print("Could not get quote for AAPL")
    
    print("Basic test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1) 