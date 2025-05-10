#!/usr/bin/env python3
"""
Webull Token Generator
This script allows you to generate and refresh authentication tokens for the Webull API
"""
import os
import sys
import json
import time
import logging
import getpass
import requests
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Webull API endpoints
BASE_URL = "https://userapi.webull.com/api"
LOGIN_URL = f"{BASE_URL}/passport/login/v5/account"
REFRESH_URL = f"{BASE_URL}/passport/refreshToken"
DEVICE_ID_URL = f"{BASE_URL}/passport/device-id"

def get_device_id():
    """Get or create a device ID for API authentication"""
    # Check if device ID is stored in a file
    device_id_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "did.bin")
    
    if os.path.exists(device_id_file):
        try:
            # Try reading as binary first
            with open(device_id_file, 'rb') as f:
                device_id_bytes = f.read().strip()
                device_id = device_id_bytes.decode('utf-8', errors='ignore')
                if device_id:
                    logger.info(f"Using existing device ID: {device_id}")
                    return device_id
        except Exception as e:
            logger.error(f"Error reading device ID file: {e}")
            # If there's an error, we'll generate a new one
    
    # Generate a new device ID
    try:
        response = requests.get(DEVICE_ID_URL)
        if response.status_code == 200:
            device_id = response.text.strip()
            
            # Save the device ID for future use
            with open(device_id_file, 'w') as f:
                f.write(device_id)
                
            logger.info(f"Generated new device ID: {device_id}")
            return device_id
        else:
            logger.error(f"Failed to get device ID: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting device ID: {e}")
        return None

def generate_token(username, password, device_id):
    """
    Generate a new access token by logging in
    Returns a dictionary with token information
    """
    try:
        logger.info(f"Requesting new tokens for user: {username}")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "account": username,
            "accountType": "2", # 2 = email
            "deviceId": device_id,
            "deviceName": "Webull Kill Switch",
            "password": password,
            "regionId": "1" # 1 = US
        }
        
        response = requests.post(LOGIN_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for successful login
            if 'accessToken' in result:
                # Create token data structure
                token_data = {
                    'access_token': result['accessToken'],
                    'refresh_token': result.get('refreshToken'),
                    'token_expiry': (datetime.now() + timedelta(hours=24)).isoformat(),
                    'user_id': result.get('userId'),
                    'device_id': device_id,
                    'last_updated': datetime.now().isoformat()
                }
                
                # Save the token data
                token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webull_token.json")
                with open(token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                logger.info("Successfully generated and saved authentication tokens")
                return token_data
            else:
                logger.error(f"Login failed: {result.get('msg', 'Unknown error')}")
                return None
        else:
            logger.error(f"Login request failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        return None

def refresh_token():
    """
    Refresh an existing access token
    Returns the refreshed token data or None if refresh fails
    """
    try:
        # Load existing token data
        token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webull_token.json")
        
        if not os.path.exists(token_file):
            logger.error("No token file found. Please generate a new token first.")
            return None
        
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        refresh_token = token_data.get('refresh_token')
        device_id = token_data.get('device_id')
        
        if not refresh_token or not device_id:
            logger.error("Invalid token data. Missing refresh token or device ID.")
            return None
        
        logger.info("Refreshing access token")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'refreshToken': refresh_token,
            'deviceId': device_id
        }
        
        response = requests.post(REFRESH_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'accessToken' in result:
                # Update token data
                token_data['access_token'] = result['accessToken']
                
                # Update refresh token if provided
                if 'refreshToken' in result:
                    token_data['refresh_token'] = result['refreshToken']
                
                # Update expiry and timestamp
                token_data['token_expiry'] = (datetime.now() + timedelta(hours=24)).isoformat()
                token_data['last_updated'] = datetime.now().isoformat()
                
                # Save updated token data
                with open(token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                logger.info("Successfully refreshed authentication tokens")
                return token_data
            else:
                logger.error(f"Token refresh response missing access token: {result}")
                return None
        else:
            logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate or refresh Webull API tokens')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate token command
    generate_parser = subparsers.add_parser('generate', help='Generate new tokens')
    generate_parser.add_argument('--username', help='Webull account username/email')
    generate_parser.add_argument('--password', help='Webull account password')
    
    # Refresh token command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh existing tokens')
    
    # Show token info command
    info_parser = subparsers.add_parser('info', help='Show current token information')
    
    return parser.parse_args()

def show_token_info():
    """Display information about the current token"""
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webull_token.json")
    
    if not os.path.exists(token_file):
        print("No token file found.")
        return
    
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        print("\n=== Webull Token Information ===")
        print(f"User ID: {token_data.get('user_id', 'Not available')}")
        print(f"Device ID: {token_data.get('device_id', 'Not available')}")
        
        # Show access token (partially masked)
        access_token = token_data.get('access_token', '')
        if access_token:
            masked_token = access_token[:5] + '*' * (len(access_token) - 10) + access_token[-5:]
            print(f"Access Token: {masked_token}")
        else:
            print("Access Token: Not available")
        
        # Show expiry information
        try:
            expiry = datetime.fromisoformat(token_data.get('token_expiry', ''))
            now = datetime.now()
            
            if expiry > now:
                time_left = expiry - now
                print(f"Expires in: {time_left.total_seconds() / 3600:.1f} hours")
                print(f"Expiry: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"Token EXPIRED: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            print("Expiry: Unknown")
        
        # Show last updated time
        try:
            last_updated = datetime.fromisoformat(token_data.get('last_updated', ''))
            print(f"Last Updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            print("Last Updated: Unknown")
        
        print("================================\n")
    except Exception as e:
        print(f"Error reading token file: {e}")

def load_env_file():
    """Load credentials from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_vars = {}
    
    if os.path.exists(env_file):
        logger.info(f"Loading credentials from .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars
    else:
        logger.warning(f".env file not found at {env_file}")
        return {}

def generate_new_token():
    """
    Generate a new authentication token for Webull API
    Requires login credentials
    """
    # First try to load from .env file
    env_vars = load_env_file()
    
    # Get username/email and password from environment variables
    username = env_vars.get('WEBULL_USERNAME') or os.environ.get('WEBULL_USERNAME')
    password = env_vars.get('WEBULL_PASSWORD') or os.environ.get('WEBULL_PASSWORD')
    
    if not username:
        # Fall back to user input if environment variable not set
        username = input("Enter Webull username/email: ")
    
    if not password:
        # Fall back to user input if environment variable not set
        password = getpass.getpass("Enter Webull password: ")
    
    # Get or generate device ID
    device_id = get_device_id()
    logger.info(f"Using device ID: {device_id}")
    
    # Generate token
    token_data = generate_token(username, password, device_id)
    if token_data:
        print("Successfully generated new authentication tokens")
        show_token_info()
    else:
        print("Failed to generate tokens")

def main():
    """Main function"""
    args = parse_arguments()
    
    # Default to info command if none specified
    if not args.command:
        args.command = 'info'
    
    if args.command == 'generate':
        generate_new_token()
    
    elif args.command == 'refresh':
        token_data = refresh_token()
        if token_data:
            print("Successfully refreshed authentication tokens")
            show_token_info()
        else:
            print("Failed to refresh tokens")
    
    elif args.command == 'info':
        show_token_info()

if __name__ == "__main__":
    main() 