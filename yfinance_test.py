#!/usr/bin/env python3
import sys
import traceback

try:
    print("This is a test script using yfinance API")
    print("First, let's install yfinance if needed...")
    
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    
    print("Importing yfinance...")
    import yfinance as yf
    print("yfinance imported successfully.")
    
    print("Getting AAPL data...")
    aapl = yf.Ticker("AAPL")
    
    # Print current price
    info = aapl.info
    print(f"AAPL current price: ${info.get('regularMarketPrice', 'N/A')}")
    
    # Print some basic stock info
    print(f"Company name: {info.get('longName', 'N/A')}")
    print(f"Market cap: ${info.get('marketCap', 'N/A'):,}")
    
    print("yfinance test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1) 