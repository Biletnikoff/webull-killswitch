#!/usr/bin/env python3
"""
Advanced script to search for and extract Webull tokens from various sources
"""
import os
import sys
import json
import re
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta

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

def search_file_for_tokens(file_path):
    """Search a file for access tokens and refresh tokens"""
    try:
        if not os.path.exists(file_path):
            return None
            
        # Don't read binary files or large files
        if os.path.getsize(file_path) > 10 * 1024 * 1024:  # > 10MB
            return None
            
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
            
            # Define regex patterns for different token formats
            token_patterns = {
                "access_token": r'"access[tT]oken"\s*:\s*"([^"]+)"',
                "refresh_token": r'"refresh[tT]oken"\s*:\s*"([^"]+)"',
                "device_id": r'"(deviceId|did)"\s*:\s*"([^"]+)"',
                "user_id": r'"(userId|secAccountId|accountId)"\s*:\s*"?(\d+)"?'
            }
            
            results = {}
            
            for key, pattern in token_patterns.items():
                match = re.search(pattern, content)
                if match:
                    if key == "device_id" or key == "user_id":
                        # These patterns have a group for the field name and a group for the value
                        results[key] = match.group(2)
                    else:
                        results[key] = match.group(1)
            
            if results:
                logger.info(f"Found token info in {file_path}: {list(results.keys())}")
                return results
            else:
                return None
    except Exception as e:
        logger.error(f"Error searching file {file_path}: {str(e)}")
        return None

def search_sqlite_db(db_path):
    """Search a SQLite database for token information"""
    try:
        if not os.path.exists(db_path):
            return None
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        results = {}
        
        # Loop through tables looking for token-related columns
        for table in tables:
            table_name = table[0]
            try:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Look for token-related columns
                token_columns = []
                for col in column_names:
                    if 'token' in col.lower() or 'access' in col.lower() or 'refresh' in col.lower():
                        token_columns.append(col)
                
                if token_columns:
                    # Get values from token columns
                    query = f"SELECT {', '.join(token_columns)} FROM {table_name} LIMIT 10;"
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    if rows:
                        for i, row in enumerate(rows):
                            for j, value in enumerate(row):
                                if value and isinstance(value, str) and len(value) > 20:
                                    # This looks like a token
                                    column = token_columns[j]
                                    logger.info(f"Found possible token in {db_path}, table {table_name}, column {column}")
                                    
                                    if 'access' in column.lower() or 'token' in column.lower() and 'refresh' not in column.lower():
                                        results['access_token'] = value
                                    elif 'refresh' in column.lower():
                                        results['refresh_token'] = value
            except Exception as e:
                logger.warning(f"Error querying table {table_name}: {str(e)}")
                continue
                
        conn.close()
        return results if results else None
    except Exception as e:
        logger.error(f"Error searching database {db_path}: {str(e)}")
        return None

def search_for_tokens():
    """Search for Webull tokens in various locations"""
    # Known locations to search
    webull_folders = [
        os.path.expanduser("~/Library/Application Support/Webull Desktop"),
        os.path.expanduser("~/Library/Application Support/Webull"),
        os.path.expanduser("~/Library/Application Support/Webull Desktop/Webull Desktop"),
        os.path.expanduser("~/Library/Caches/Webull Desktop"),
        os.path.expanduser("~/Library/Cookies")
    ]
    
    # Sqlite databases to check
    db_files = []
    # Text files to check
    text_files = []
    
    # Discover files to search
    for folder in webull_folders:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith('.db') or file.endswith('.sqlite'):
                        db_files.append(file_path)
                    elif file.endswith('.json') or file.endswith('.txt') or file.endswith('.ini'):
                        text_files.append(file_path)
    
    # Add browser cookie databases
    chrome_cookies = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies")
    if os.path.exists(chrome_cookies):
        db_files.append(chrome_cookies)
    
    safari_cookies = os.path.expanduser("~/Library/Cookies/Cookies.binarycookies")
    if os.path.exists(safari_cookies):
        db_files.append(safari_cookies)
    
    # Check specific known locations
    settings_db = os.path.expanduser("~/Library/Application Support/Webull Desktop/Webull Desktop/settings/settings.db")
    if os.path.exists(settings_db):
        logger.info(f"Found Webull settings database: {settings_db}")
        db_files.insert(0, settings_db)  # Prioritize this file
    
    settings_json = os.path.expanduser("~/Library/Application Support/Webull Desktop/Webull Desktop/settings/settings.json")
    if os.path.exists(settings_json):
        logger.info(f"Found Webull settings JSON: {settings_json}")
        text_files.insert(0, settings_json)  # Prioritize this file
    
    # Found token information
    token_info = {}
    
    # Search text files
    logger.info(f"Searching {len(text_files)} text files for tokens...")
    for file_path in text_files:
        results = search_file_for_tokens(file_path)
        if results:
            # Add new tokens to our collection
            for key, value in results.items():
                if key not in token_info:
                    token_info[key] = value
    
    # Search databases
    logger.info(f"Searching {len(db_files)} databases for tokens...")
    for db_path in db_files:
        results = search_sqlite_db(db_path)
        if results:
            # Add new tokens to our collection
            for key, value in results.items():
                if key not in token_info:
                    token_info[key] = value
    
    return token_info

def test_advanced_token_extraction():
    """Test advanced token extraction from various sources"""
    print("\n=== Advanced Token Extraction from Webull Sources ===\n")
    
    # First try the built-in method
    auth = WebullAuth()
    print("1. Trying built-in WebullAuth.extract_token_from_webull() method...")
    if auth.extract_token_from_webull():
        print("✅ Built-in method succeeded!")
        print(f"Access Token: {auth.access_token[:10]}..." if auth.access_token else "Access Token: None")
        print(f"Refresh Token: {auth.refresh_token[:10]}..." if auth.refresh_token else "Refresh Token: None")
        print(f"Token saved to: {auth.token_file}")
        print("\n=== Test Complete ===")
        return True
        
    print("❌ Built-in method failed. Trying advanced search...")
    
    # Search for tokens in various locations
    print("\n2. Searching for tokens in files and databases...")
    token_info = search_for_tokens()
    
    if not token_info:
        print("❌ No token information found in any location.")
        print("\n=== Test Complete ===")
        return False
    
    # Display found tokens
    print("\n✅ Found token information:")
    for key, value in token_info.items():
        if value:
            if key in ['access_token', 'refresh_token']:
                print(f"{key}: {value[:10]}...")
            else:
                print(f"{key}: {value}")
    
    # Update WebullAuth with found tokens
    print("\n3. Updating WebullAuth with found tokens...")
    if 'access_token' in token_info:
        # We have enough to update the auth
        try:
            # Create token expiry (24 hours from now)
            token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
            
            # Update token_data
            auth.token_data["access_token"] = token_info.get('access_token')
            if 'refresh_token' in token_info:
                auth.token_data["refresh_token"] = token_info.get('refresh_token')
            if 'user_id' in token_info:
                auth.token_data["user_id"] = token_info.get('user_id')
            if 'device_id' in token_info:
                auth.token_data["device_id"] = token_info.get('device_id')
            auth.token_data["token_expiry"] = token_expiry
            auth.token_data["last_updated"] = datetime.now().isoformat()
            
            # Save the token data
            if auth._save_token_to_file():
                print("✅ Successfully saved token data to file!")
                print(f"Token saved to: {auth.token_file}")
                return True
            else:
                print("❌ Failed to save token data to file.")
                return False
        except Exception as e:
            print(f"❌ Error updating token data: {str(e)}")
            return False
    else:
        print("❌ No access token found. Cannot update WebullAuth.")
        return False

if __name__ == "__main__":
    test_advanced_token_extraction() 