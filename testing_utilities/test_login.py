#!/usr/bin/env python3
import os
import sys
import logging
import traceback
from dotenv import load_dotenv
from webull import webull

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger()

def test_login():
    """Test login to Webull account using credentials from .env file"""
    try:
        # Load environment variables
        logger.info("Loading environment variables...")
        load_dotenv()
        
        # Create webull instance
        logger.info("Creating Webull instance...")
        wb = webull()
        
        # Check for authentication method
        if os.getenv('WEBULL_TOKEN'):
            # Use token authentication
            logger.info("Found token in .env file")
            logger.info("Attempting to login with token...")
            try:
                wb.login_by_token(os.getenv('WEBULL_TOKEN'))
                logger.info("Token login successful")
            except Exception as e:
                logger.error(f"Token login failed: {e}")
                traceback.print_exc()
                return False
        else:
            # Use email/password authentication
            email = os.getenv('WEBULL_EMAIL')
            password = os.getenv('WEBULL_PASSWORD')
            
            if not email or not password:
                logger.error("Webull email and password must be provided in .env file")
                logger.error(f"Email found: {'Yes' if email else 'No'}")
                logger.error(f"Password found: {'Yes' if password else 'No'}")
                return False
            
            logger.info(f"Attempting to login with email: {email}")
            
            # Get MFA code if needed
            try:
                logger.info("Checking if MFA is required...")
                try:
                    mfa_required = wb.get_mfa(email)
                    logger.info(f"MFA required: {mfa_required}")
                except Exception as e:
                    logger.error(f"Error checking MFA: {e}")
                    traceback.print_exc()
                    return False
                
                if mfa_required:
                    logger.info("MFA required. Code has been sent to your device.")
                    mfa_code = input("Enter MFA code sent to your device: ")
                    wb.login(email, password, mfa_code)
                    logger.info("Login with MFA successful")
                else:
                    logger.info("MFA not required, logging in with email/password...")
                    wb.login(email, password)
                    logger.info("Login successful (no MFA required)")
            except Exception as e:
                logger.error(f"Login failed: {e}")
                traceback.print_exc()
                return False
        
        # Verify login by getting account info
        try:
            logger.info("Verifying login by getting account ID...")
            account_id = wb.get_account_id()
            logger.info(f"Successfully logged in. Account ID: {account_id}")
            
            # Get account details
            logger.info("Fetching account details...")
            account = wb.get_account()
            if account:
                logger.info("Account details retrieved successfully")
                net_liquidation = account.get('netLiquidation', 'N/A')
                logger.info(f"Account net liquidation: ${net_liquidation}")
                
                # Show positions if any
                logger.info("Fetching positions...")
                positions = wb.get_positions()
                if positions:
                    logger.info(f"Found {len(positions)} positions:")
                    for i, pos in enumerate(positions, 1):
                        symbol = pos.get('ticker', {}).get('symbol', 'Unknown')
                        quantity = pos.get('position', 'N/A')
                        market_value = pos.get('marketValue', 'N/A')
                        logger.info(f"  {i}. {symbol}: {quantity} shares, Market Value: ${market_value}")
                else:
                    logger.info("No open positions found")
            else:
                logger.warning("Could not retrieve account details")
                
            return True
        except Exception as e:
            logger.error(f"Failed to verify login: {e}")
            traceback.print_exc()
            return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_login()
    if success:
        logger.info("Login test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Login test failed!")
        sys.exit(1) 