#!/usr/bin/env python3
"""
Token Refresh Test Script
Tests the automatic token refresh mechanism for the Webull Kill Switch
"""
import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our webull auth module
try:
    from webull_auth import refresh_auth, get_auth_headers, webull_auth, WebullAuth
    from generate_token import show_token_info
    WEBULL_AUTH_AVAILABLE = True
except ImportError:
    logger.error("webull_auth module not found. Please make sure it's properly installed.")
    WEBULL_AUTH_AVAILABLE = False
    sys.exit(1)

def simulate_api_call_with_403():
    """
    Simulate an API call that returns a 403 error
    """
    logger.info("Simulating API call...")
    
    # Force token to appear expired
    original_expiry = webull_auth.token_expiry
    if webull_auth.token_expiry:
        # Artificially expire the token
        webull_auth.token_expiry = (datetime.now() - timedelta(hours=1)).isoformat()
        logger.info(f"Artificially expired token (was: {original_expiry}, now: {webull_auth.token_expiry})")
    
    # Try to get headers, which should trigger a refresh
    try:
        logger.info("Testing get_auth_headers() with expired token...")
        headers = get_auth_headers()
        
        if headers and 'Authorization' in headers:
            logger.info("✅ Successfully got headers after token refresh")
            return True
        else:
            logger.error("❌ Failed to get valid headers")
            return False
    except Exception as e:
        logger.error(f"❌ Error during API call simulation: {e}")
        return False
    finally:
        # Restore original expiry if we modified it
        if original_expiry:
            webull_auth.token_expiry = original_expiry

def test_direct_refresh():
    """
    Test directly calling the refresh function
    """
    logger.info("Testing direct token refresh...")
    
    # Save original token info
    original_token = webull_auth.access_token
    original_expiry = webull_auth.token_expiry
    
    # Perform the refresh
    try:
        result = refresh_auth()
        
        if result:
            logger.info("✅ Token refresh successful")
            
            # Verify token changed
            if original_token != webull_auth.access_token:
                logger.info("✅ Token value changed after refresh")
            else:
                logger.warning("⚠️ Token value remained unchanged")
                
            # Verify expiry extended
            try:
                old_expiry = datetime.fromisoformat(original_expiry) if original_expiry else datetime.now()
                new_expiry = datetime.fromisoformat(webull_auth.token_expiry) if webull_auth.token_expiry else datetime.now()
                
                if new_expiry > old_expiry:
                    logger.info(f"✅ Token expiry extended by {(new_expiry - old_expiry).total_seconds() / 3600:.1f} hours")
                else:
                    logger.warning("⚠️ Token expiry not extended")
            except:
                logger.warning("⚠️ Could not parse expiry dates")
            
            return True
        else:
            logger.error("❌ Token refresh failed")
            return False
    except Exception as e:
        logger.error(f"❌ Error during direct refresh: {e}")
        return False

def simulate_monitor_handling_403():
    """
    Simulate the monitor script's handling of 403 errors
    """
    logger.info("Simulating how monitor handles 403 errors...")
    
    # Import the function to test from the monitor script
    try:
        from monitor_pnl_hardened import refresh_auth_token, get_account_pnl, global_args
        
        # Initialize global_args if needed
        if global_args is None:
            class Args:
                def __init__(self):
                    self.test = True
                    self.verbose = True
                    self.threshold = -300
                    self.interval = 5
            
            # Set global args
            import monitor_pnl_hardened
            monitor_pnl_hardened.global_args = Args()
        
        # Simulate an auth failure with the monitor's functions
        # Modify the token expiry temporarily
        original_expiry = webull_auth.token_expiry
        webull_auth.token_expiry = (datetime.now() - timedelta(hours=1)).isoformat()
        
        try:
            # Test if the monitor's refresh function works
            logger.info("Testing monitor's refresh_auth_token()...")
            result = refresh_auth_token()
            
            if result:
                logger.info("✅ Monitor's token refresh successful")
            else:
                logger.error("❌ Monitor's token refresh failed")
            
            # Test if the monitor's PNL function handles 403 errors
            logger.info("Testing monitor's get_account_pnl() with potentially expired token...")
            pnl = get_account_pnl()
            
            if pnl is not None:
                logger.info(f"✅ Successfully got PNL value: {pnl}")
                return True
            else:
                logger.error("❌ Failed to get PNL value")
                return False
        finally:
            # Restore original expiry
            webull_auth.token_expiry = original_expiry
        
    except ImportError as e:
        logger.error(f"❌ Could not import from monitor_pnl_hardened: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error during monitor simulation: {e}")
        return False

def check_token_file():
    """
    Check if the token file exists and is valid
    """
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webull_token.json")
    
    if not os.path.exists(token_file):
        logger.error(f"❌ Token file not found at {token_file}")
        logger.info("Run 'python generate_token.py generate' to create a token file")
        return False
    
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        required_fields = ['access_token', 'refresh_token', 'token_expiry', 'device_id']
        missing_fields = [field for field in required_fields if field not in token_data]
        
        if missing_fields:
            logger.error(f"❌ Token file is missing required fields: {', '.join(missing_fields)}")
            return False
        
        # Check if token is expired
        try:
            expiry = datetime.fromisoformat(token_data.get('token_expiry', ''))
            now = datetime.now()
            
            if expiry <= now:
                logger.warning(f"⚠️ Token is expired (expired {(now - expiry).total_seconds() / 3600:.1f} hours ago)")
            else:
                logger.info(f"✅ Token is valid for {(expiry - now).total_seconds() / 3600:.1f} more hours")
        except:
            logger.warning("⚠️ Could not parse token expiry")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error checking token file: {e}")
        return False

def test_with_enhanced_test_mode():
    """
    Test the enhanced test mode feature
    """
    logger.info("Testing enhanced test mode feature...")
    
    try:
        # Get a WebullAuth instance with test mode enabled
        from webull_auth import WebullAuth
        
        # Create a new instance with test mode
        auth = WebullAuth().set_test_mode(True)
        
        # Force an error condition by using an invalid refresh token
        original_refresh_token = auth.refresh_token
        auth.refresh_token = "invalid_refresh_token"
        
        # Try to refresh the token
        logger.info("Testing refresh with invalid token but test mode enabled...")
        result = auth.refresh_access_token()
        
        if result:
            logger.info("✅ Token refresh succeeded despite invalid token (test mode working)")
            
            # Verify we got a simulated token
            if "test_refreshed_token" in auth.access_token:
                logger.info("✅ Received a simulated test token as expected")
            else:
                logger.warning(f"⚠️ Unexpected token format: {auth.access_token}")
            
            # Try API call with the test token
            logger.info("Testing API call with simulated token...")
            headers = auth.get_headers()
            if headers and headers.get("Authorization", "").startswith("Bearer test_refreshed"):
                logger.info("✅ Successfully got API headers with simulated token")
            else:
                logger.warning(f"⚠️ Unexpected headers: {headers}")
                
            # Restore original refresh token
            auth.refresh_token = original_refresh_token
            auth.save_tokens()
            return True
        else:
            logger.error("❌ Token refresh failed despite test mode being enabled")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing enhanced test mode: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test the token refresh mechanism')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--check', action='store_true', help='Check token file')
    parser.add_argument('--api', action='store_true', help='Test API call with 403 simulation')
    parser.add_argument('--refresh', action='store_true', help='Test direct token refresh')
    parser.add_argument('--monitor', action='store_true', help='Test monitor script handling')
    parser.add_argument('--test-mode', action='store_true', help='Test the enhanced test mode feature')
    
    args = parser.parse_args()
    
    # If no specific tests are requested, run all tests
    run_all = args.all or not (args.check or args.api or args.refresh or args.monitor or args.test_mode)
    
    # Header
    print("\n" + "="*70)
    print("WEBULL KILL SWITCH TOKEN REFRESH TEST")
    print("="*70)
    
    # Show token info
    print("\n[Current Token Information]")
    show_token_info()
    
    # Check token file
    if run_all or args.check:
        print("\n[Test 1: Token File Check]")
        if check_token_file():
            print("✅ Token file exists and contains required fields")
        else:
            print("❌ Token file check failed")
    
    # Test API call with 403
    if run_all or args.api:
        print("\n[Test 2: API Call with 403 Simulation]")
        if simulate_api_call_with_403():
            print("✅ Successfully handled expired token in API call")
        else:
            print("❌ API call test failed")
    
    # Test direct refresh
    if run_all or args.refresh:
        print("\n[Test 3: Direct Token Refresh]")
        if test_direct_refresh():
            print("✅ Direct token refresh successful")
        else:
            print("❌ Direct token refresh failed")
    
    # Test monitor handling
    if run_all or args.monitor:
        print("\n[Test 4: Monitor Script 403 Handling]")
        if simulate_monitor_handling_403():
            print("✅ Monitor script successfully handled 403 error")
        else:
            print("❌ Monitor script 403 handling test failed")
    
    # Test enhanced test mode
    if run_all or args.test_mode:
        print("\n[Test 5: Enhanced Test Mode]")
        if test_with_enhanced_test_mode():
            print("✅ Enhanced test mode working correctly")
        else:
            print("❌ Enhanced test mode test failed")
    
    # Show updated token info
    print("\n[Updated Token Information]")
    show_token_info()
    
    print("\nTests completed.")

if __name__ == "__main__":
    main() 