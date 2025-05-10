#!/usr/bin/env python3
import os
import sys
import traceback
from dotenv import load_dotenv

# Load .env file
print("Loading .env file...")
load_dotenv()

# Try importing the webull package
try:
    print("Importing webull package...")
    from webull import webull
    print(f"Webull package imported successfully")
except ImportError as e:
    print(f"Error importing webull package: {e}")
    sys.exit(1)

# Print Python environment info
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Create a webull instance
print("Creating Webull instance...")
wb = webull()

# Get credentials from .env
email = os.getenv('WEBULL_EMAIL')
password = os.getenv('WEBULL_PASSWORD')

print(f"Email found: {'Yes' if email else 'No'}")
print(f"Password found: {'Yes' if password and len(password) > 0 else 'No'}")

if not email or not password:
    print("WEBULL_EMAIL and WEBULL_PASSWORD not found in .env file")
    print("Current environment variables:")
    for key, value in os.environ.items():
        if 'WEBULL' in key:
            print(f"{key}=****" if 'PASSWORD' in key else f"{key}={value}")
    sys.exit(1)

# Try to get MFA
try:
    print(f"Checking if MFA is required for {email}...")
    mfa_required = wb.get_mfa(email)
    print(f"MFA required: {mfa_required}")
    
    if mfa_required:
        mfa_code = input("Enter MFA code sent to your device: ")
        print(f"Logging in with MFA code: {mfa_code}...")
        wb.login(email, password, mfa_code)
    else:
        print("Logging in with email/password...")
        wb.login(email, password)
        
    print("Login successful!")
    
    # Verify login by getting account ID
    print("Getting account ID...")
    account_id = wb.get_account_id()
    print(f"Account ID: {account_id}")
    
    print("Test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1) 