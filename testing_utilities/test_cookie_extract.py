#!/usr/bin/env python3
"""
Test script to extract Webull tokens from desktop app cookies
"""
import os
import sys
import logging

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

# Import WebullAuth
from authentication.webull_auth import WebullAuth

def test_cookie_extraction():
    """Test extracting token from Webull desktop app cookies"""
    print("\n=== Testing Token Extraction from Webull Desktop App Cookies ===\n")
    
    # Check if Webull desktop app cookie files exist
    cookie_paths = [
        os.path.expanduser("~/Library/Application Support/Webull Desktop/cookies"),
        os.path.expanduser("~/Library/Application Support/Webull/cookies")
    ]
    
    for path in cookie_paths:
        if os.path.exists(path):
            print(f"✅ Found Webull cookie file: {path}")
        else:
            print(f"❌ Webull cookie file not found: {path}")
    
    # Create WebullAuth instance
    auth = WebullAuth()
    
    # Try to extract token
    print("\nAttempting to extract token from cookies...")
    success = auth.extract_token_from_webull()
    
    if success:
        print("\n✅ Successfully extracted token from Webull desktop app cookies!")
        print(f"Access Token: {auth.access_token[:10]}..." if auth.access_token else "Access Token: None")
        print(f"Refresh Token: {auth.refresh_token[:10]}..." if auth.refresh_token else "Refresh Token: None")
        print(f"User ID: {auth.user_id}" if auth.user_id else "User ID: None")
        print(f"Device ID: {auth.device_id}" if auth.device_id else "Device ID: None")
        print(f"Token saved to: {auth.token_file}")
    else:
        print("\n❌ Failed to extract token from Webull desktop app cookies")
        print("Please ensure the Webull desktop app is installed and you are logged in")
        
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_cookie_extraction() 