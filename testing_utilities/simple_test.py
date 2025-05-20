#!/usr/bin/env python3
"""
Simple test for Webull Kill Switch
Tests authentication with our custom module
"""
import os
import sys
import traceback
import argparse
from dotenv import load_dotenv

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import our custom authentication module
try:
    print("Importing authentication module...")
    from authentication.webull_auth import WebullAuth
    print("Authentication module imported successfully")
except ImportError as e:
    print(f"Error importing authentication module: {e}")
    sys.exit(1)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Simple test for Webull authentication')
    parser.add_argument('--no-kill', action='store_true', help='Do not execute kill switch')
    args = parser.parse_args()

    # Load .env file
    print("Loading .env file...")
    load_dotenv()

    # Print Python environment info
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")

    # Create a WebullAuth instance
    print("Creating WebullAuth instance...")
    auth = WebullAuth()

    # Check if token is valid
    print("Checking if token is valid...")
    if auth.is_token_valid():
        print("✅ Token is valid")
        token_data = auth.token_data
        print(f"User ID: {token_data.get('user_id')}")
        print(f"Token expiry: {token_data.get('token_expiry')}")
    else:
        print("❌ Token is not valid, refresh needed")
        
        # Try to refresh token
        print("Attempting to refresh token...")
        if auth.refresh_auth_token():
            print("✅ Token refreshed successfully")
        else:
            print("❌ Failed to refresh token")
            print("You may need to run update_token.py to manually update the token")
            
    # Get auth headers
    print("Getting authentication headers...")
    headers = auth.get_auth_headers()
    print(f"Headers generated: {len(headers)} items")
    
    print("Test completed successfully!")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1) 