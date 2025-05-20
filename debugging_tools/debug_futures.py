#!/usr/bin/env python3
import os
import json
import logging
from dotenv import load_dotenv
from webull import webull

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Futures account ID
FUTURES_ACCOUNT_ID = os.getenv('FUTURES_ACCOUNT_ID', 'CUX3WUH5')

def main():
    """Debug script to examine the structure of futures account data"""
    try:
        # Create Webull instance and login
        logger.info("Logging into Webull...")
        wb = webull()
        
        email = os.getenv('WEBULL_EMAIL')
        password = os.getenv('WEBULL_PASSWORD')
        
        if not email or not password:
            logger.error("Email or password not found in .env file")
            return
            
        mfa_required = wb.get_mfa(email)
        if mfa_required:
            logger.info("MFA required, please enter code:")
            mfa_code = input("MFA code: ")
            wb.login(email, password, mfa_code)
        else:
            wb.login(email, password)
            
        logger.info("Login successful")
        
        # Try to get futures account data
        logger.info(f"Getting futures account data for {FUTURES_ACCOUNT_ID}...")
        try:
            futures_data = wb.get_futures_account(FUTURES_ACCOUNT_ID)
            
            if futures_data:
                logger.info("Successfully retrieved futures account data")
                
                # Save raw data to file
                with open('futures_data_raw.json', 'w') as f:
                    json.dump(futures_data, f, indent=2)
                logger.info("Saved raw futures data to futures_data_raw.json")
                
                # Print structure overview
                logger.info("Futures account data structure:")
                if isinstance(futures_data, dict):
                    for key, value in futures_data.items():
                        val_type = type(value).__name__
                        val_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        logger.info(f"  {key} ({val_type}): {val_preview}")
                        
                        # If this is a nested dict or list, show one more level
                        if isinstance(value, dict) and value:
                            for subkey in value:
                                logger.info(f"    - {subkey}")
                        elif isinstance(value, list) and value:
                            logger.info(f"    - {len(value)} items")
                            if len(value) > 0 and isinstance(value[0], dict):
                                for subkey in value[0]:
                                    logger.info(f"      - {subkey}")
                else:
                    logger.info(f"Data is not a dictionary: {type(futures_data)}")
                
                # Look for specific P/L related fields
                logger.info("Searching for P/L related fields:")
                pnl_found = False
                
                pnl_keys = ['unrealizedPL', 'unrealizedProfit', 'dayPnl', 'dailyPnL', 
                            'dayPL', 'dayProfit', 'unRlsProfit', 'dailyUnrealizedProfit']
                
                for key in pnl_keys:
                    if key in futures_data:
                        pnl_found = True
                        logger.info(f"  Found P/L field: {key} = {futures_data[key]}")
                
                if not pnl_found:
                    logger.info("  No P/L fields found in top level")
                    
                    # Try searching recursively in nested structures
                    def search_nested(data, prefix=""):
                        found = False
                        if isinstance(data, dict):
                            for k, v in data.items():
                                path = f"{prefix}.{k}" if prefix else k
                                if any(pnl_key in k.lower() for pnl_key in ['pnl', 'profit', 'loss']):
                                    logger.info(f"  Found P/L related field: {path} = {v}")
                                    found = True
                                found_nested = search_nested(v, path)
                                found = found or found_nested
                        elif isinstance(data, list) and data:
                            for i, item in enumerate(data[:3]):  # Check first 3 items
                                path = f"{prefix}[{i}]"
                                found_nested = search_nested(item, path)
                                found = found or found_nested
                        return found
                    
                    nested_found = search_nested(futures_data)
                    if not nested_found:
                        logger.info("  No P/L related fields found in nested structures")
            else:
                logger.error("No data returned for futures account")
        
        except Exception as e:
            logger.error(f"Error getting futures account data: {e}")
            
        # Try to get account ID
        try:
            logger.info("Getting default account ID...")
            account_id = wb.get_account_id()
            logger.info(f"Default account ID: {account_id}")
        except Exception as e:
            logger.error(f"Error getting account ID: {e}")
            
        # Try other account-related methods
        try:
            logger.info("Getting account details...")
            account = wb.get_account()
            if account:
                logger.info("Account details:")
                for key, value in account.items():
                    val_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    logger.info(f"  {key}: {val_preview}")
                
                # Save account data
                with open('account_data.json', 'w') as f:
                    json.dump(account, f, indent=2)
                logger.info("Saved account data to account_data.json")
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        
if __name__ == "__main__":
    main() 