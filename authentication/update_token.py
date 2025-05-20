#!/usr/bin/env python3
"""
Tool for updating Webull authentication token
Supports updating from browser data or token files
"""
import os
import sys
import argparse
import logging
import json
from getpass import getpass
from webull_auth import WebullAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(description='Update Webull token from browser data')
    parser.add_argument('--file', '-f', help='Path to a file containing token JSON or headers')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    return parser

def print_instructions():
    """Print instructions for obtaining token information from browser"""
    print("\nInstructions for updating Webull token:")
    print("=======================================")
    print("1. Log into Webull in your browser at https://app.webull.com/")
    print("2. Open Developer Tools (F12 or Ctrl+Shift+I or Cmd+Option+I on Mac)")
    print("3. Go to the Network tab in Developer Tools")
    print("4. Refresh the page or perform any action")
    print("5. Look for any API requests in the Network tab (filter for 'api' or 'trading')")
    print("6. Click on a request to Webull API (like 'account', 'user', or 'trading')")
    print("\nEASIEST METHOD FOR ALL BROWSERS:")
    print("   - Right-click the request and select 'Copy' > 'Copy as cURL'")
    print("   - This will copy all headers at once, including the token")
    print("   - Paste the entire curl command when prompted below")
    
    print("\nAlternatively, you can copy specific headers individually:")
    print("\nIn Chrome:")
    print("   - Select the 'Headers' tab of the request")
    print("   - Find the 'Request Headers' section")
    print("   - Look for 'access_token', 'authorization', or 't_token' header")
    print("   - Also look for 'did' header (device ID)")
    print("   - Copy these headers with their values")
    
    print("\nIn Firefox:")
    print("   - Select the 'Headers' tab of the request")
    print("   - Look for the 'Request Headers' section")
    print("   - Right-click and use 'Copy Value' on these important headers:")
    print("     - access_token or authorization or t_token")
    print("     - did (device ID)")
    
    print("\nIn Safari:")
    print("   - Click on the 'Headers' tab of the request")
    print("   - Find the 'Request Headers' section")
    print("   - Copy these important headers with their values as 'header: value':")
    print("     - access_token or authorization or t_token")
    print("     - did (device ID)")
    
    print("\nTOKEN INFORMATION TO LOOK FOR:")
    print("   - The token will be in one of these headers:")
    print("     1. access_token - Usually starts with 'dc_us_tech...'")
    print("     2. authorization - May be in format 'Bearer TOKEN' or just the token")
    print("     3. t_token - In newer Webull web interface")
    
    print("\n7. Paste the copied headers or cURL command when prompted below")
    print("   If you saved to a file, restart this script with: ./update_token.py -f your_file.txt")
    print("\nNOTE: The token will expire after 24 hours. You'll need to update it again after that time.\n")

def read_multiline_input():
    """Read multiline input from user until EOF (Ctrl+D) or 'END' on a new line"""
    print("\nEnter/paste your token data (end with Ctrl+D or type 'END' on a new line):")
    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)

def read_token_from_file(file_path):
    """Read token data from a file"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def main():
    """Main function to process command line arguments"""
    parser = setup_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.file:
        # Read token data from file
        logger.info(f"Reading token data from file: {args.file}")
        token_data = read_token_from_file(args.file)
        if not token_data:
            logger.error("Failed to read token data from file.")
            print(f"Error: Could not read token data from file {args.file}")
            return 1
        print(f"Read token data from file {args.file}")
    else:
        # Show instructions and get token data from user input
        print_instructions()
        print("\n" + "="*80)
        print("PASTE TOKEN DATA BELOW (press Ctrl+D or type 'END' on a new line when finished):")
        print("="*80)
        token_data = read_multiline_input()
        
        if not token_data or token_data.strip() == "":
            logger.error("No token data provided.")
            print("Error: No token data provided. Please try again.")
            return 1
        
    # Update token data in WebullAuth
    try:
        auth = WebullAuth()
        success = auth.update_token_from_browser_data(token_data)
        if success:
            print("\n" + "="*80)
            print("TOKEN UPDATED SUCCESSFULLY!".center(80))
            print("="*80)
            print(f"\nToken has been saved to: {auth.token_file}")
            print(f"Access Token: {auth.access_token[:10]}..." if auth.access_token else "Access Token: None")
            print(f"User ID: {auth.user_id}" if auth.user_id else "User ID: None")
            print(f"Device ID: {auth.device_id}" if auth.device_id else "Device ID: None")
            print(f"Token will expire in approximately 24 hours.")
            print("\nYou can now run the monitor script:")
            print("python3 monitor_pnl_hardened.py --test")
            return 0
        else:
            print("\n" + "="*80)
            print("TOKEN UPDATE FAILED".center(80))
            print("="*80)
            print("\nCould not extract valid token data from the provided input.")
            print("Please check that you've copied the correct headers or token JSON.")
            print("You can also try running with --verbose for more detailed error messages.")
            return 1
    except Exception as e:
        logger.error(f"Error updating token: {str(e)}")
        print(f"\nError updating token: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 