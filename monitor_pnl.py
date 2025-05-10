#!/usr/bin/env python3
import os
import time
import subprocess
import logging
import json
import datetime
import sys
import uuid
from dotenv import load_dotenv
from webull import webull

# Load environment variables from .env file
load_dotenv()

# Global flag to track if a new token is needed
SHOULD_REQUEST_NEW_TOKEN = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

# Load headers configuration from environment variables
def load_webull_configs():
    """Load all Webull configuration values from environment variables"""
    global WEBULL_HEADERS
    
    # Initialize headers dictionary
    WEBULL_HEADERS = {
        'did': os.getenv('WEBULL_DID', 'z7e2nia9wl6g9qmrwqwqp8eraogg7khi'),
        't_token': os.getenv('WEBULL_T_TOKEN', '196b7894b94-3fd6050b56d2496181b94e2135c87723'),
        'x_s': os.getenv('WEBULL_X_S', '9032a58e9efde1ac2baec1e01c6c2747f2d654e1ce7d520e4a1ec3f2b63ab495'),
        'x_sv': os.getenv('WEBULL_X_SV', 'xodp2vg9'),
        'osv': os.getenv('WEBULL_OSV', 'i9zh'),
        'referer': os.getenv('WEBULL_REFERER', 'https://www.webull.com/center'),
        'user_agent': os.getenv('WEBULL_USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36')
    }
    
    # Log loaded headers (without sensitive values)
    logger.info("Loaded Webull configuration headers")
    return WEBULL_HEADERS

# Helper function to parse env values and strip comments
def get_env_value(key, default, convert_func=str):
    value = os.getenv(key, default)
    if value and '#' in value:
        value = value.split('#')[0].strip()
    try:
        return convert_func(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing {key}: {e}, using default: {default}")
        return convert_func(default)

# Configuration
THRESHOLD = get_env_value('PNL_THRESHOLD', '-500', float)
THRESHOLD_TYPE = get_env_value('THRESHOLD_TYPE', 'DOLLAR', str).upper()
CHECK_INTERVAL = get_env_value('CHECK_INTERVAL', '60', int)
SCRIPT_PATH = os.path.expanduser(get_env_value('KILL_SCRIPT_PATH', 'killTradingApp.scpt', str))
SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)  # Normalize path

# Ensure the kill script exists
if not os.path.exists(SCRIPT_PATH):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SCRIPT_PATH = os.path.join(current_dir, 'killTradingApp.scpt')
    if not os.path.exists(SCRIPT_PATH):
        raise FileNotFoundError(f"Kill script not found at {SCRIPT_PATH}")

# Session token file path
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webull_token.json')

def trigger_kill():
    """
    Execute the AppleScript to close Webull Desktop 8.12 and related Chrome tabs
    This will:
    1. Close Webull Desktop 8.12
    2. Close all Chrome tabs containing 'webull.com'
    """
    try:
        if not os.path.exists(SCRIPT_PATH):
            logger.error(f"Kill script not found at {SCRIPT_PATH}")
            return False
            
        logger.info(f"Executing kill script: {SCRIPT_PATH}")
        result = subprocess.run(['osascript', SCRIPT_PATH], 
                              capture_output=True, text=True, check=True)
        
        # Log the detailed output from the kill script
        if result.stdout:
            logger.info("Kill script output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
            
            # Check if Webull was successfully closed
            if "Successfully sent quit command to Webull Desktop" in result.stdout or "Successfully quit Webull Desktop" in result.stdout:
                logger.info("Webull Desktop application was successfully closed")
                send_notification("Kill Switch Success", "Webull Desktop application was closed successfully", True)
            elif "Error quitting Webull Desktop" in result.stdout:
                logger.warning("There were errors closing Webull Desktop - check logs for details")
                send_notification("Kill Switch Warning", "There were errors closing Webull Desktop", True)
            else:
                logger.info("Kill script executed but no confirmation of Webull Desktop closure")
                send_notification("Kill Switch Executed", "Kill script executed - check logs for details", True)
            
            # Log Chrome tab closures
            if "Closed " in result.stdout and " Chrome tabs" in result.stdout:
                try:
                    tabs_part = result.stdout.split("Closed ")[1].split(" Chrome tabs")[0]
                    tabs_closed = int(tabs_part)
                    if tabs_closed > 0:
                        logger.info(f"Closed {tabs_closed} Chrome tabs with webull.com")
                except (IndexError, ValueError):
                    pass
        
        logger.info("Kill script executed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing kill script: {e}")
        if e.stderr:
            logger.error(f"Script error: {e.stderr}")
        if e.stdout:
            logger.error(f"Script output: {e.stdout}")
        send_notification("Kill Switch Error", "Failed to execute kill script", True)
        return False

def save_token(wb, token_data=None):
    """Save the current Webull session token to a file"""
    try:
        if token_data is None:
            token_data = {
                'refreshToken': wb._refresh_token,
                'accessToken': wb._access_token,
                'tokenExpireTime': wb._token_expire,
                'uuid': wb._uuid
            }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
            
        logger.info("Webull token saved to file")
        return True
    except Exception as e:
        logger.warning(f"Failed to save token: {e}")
        return False

def load_token(wb):
    """Load a previously saved Webull session token"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
                
            wb._refresh_token = token_data.get('refreshToken')
            wb._access_token = token_data.get('accessToken')
            wb._token_expire = token_data.get('tokenExpireTime')
            wb._uuid = token_data.get('uuid')
            
            logger.info("Loaded saved token")
            return True
        else:
            logger.info("No saved token found")
            return False
    except Exception as e:
        logger.warning(f"Failed to load token: {e}")
        return False

def token_is_expired(token_expire):
    """Check if a token is expired"""
    if not token_expire:
        return True
    
    try:
        # Convert the token expiration string to a datetime object
        if isinstance(token_expire, str):
            # Format is like "2021-02-14T13:35:35.780+0000"
            # Remove the timezone part for simplicity
            token_expire = token_expire.split('+')[0].split('.')[0]
            expire_dt = datetime.datetime.fromisoformat(token_expire)
        else:
            # Assume it's a timestamp in milliseconds
            expire_dt = datetime.datetime.fromtimestamp(token_expire / 1000)
        
        # Add some buffer (5 minutes)
        now_with_buffer = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        return now_with_buffer >= expire_dt
    except Exception as e:
        logger.warning(f"Error checking token expiration: {e}")
        return True  # Assume expired if there's an error

def manual_token_setup():
    """
    Guide the user through manually setting up the token from the Webull web app.
    Returns True if successful, False otherwise.
    """
    print("\n" + "="*80)
    print("MANUAL TOKEN SETUP REQUIRED")
    print("="*80)
    print("\nWebull now requires image verification which prevents automated login.")
    print("To continue, you'll need to manually get a token from the Webull web app.")
    print("\nFollow these steps:")
    print("1. Visit https://app.webull.com/ in Chrome's Incognito mode")
    print("2. Log in with your credentials")
    print("3. Open Chrome DevTools (F12 or Right-click > Inspect)")
    print("4. Go to the Network tab")
    print("5. Filter for 'refreshToken'")
    print("6. Find a request with the tokens in the response")
    print("7. Copy the entire JSON response that contains:")
    print("   - accessToken")
    print("   - refreshToken")
    print("   - tokenExpireTime")
    print("   - uuid")
    print("\nPaste the JSON below (or type 'exit' to quit):\n")
    
    token_json = ""
    print("> ", end="")
    
    while True:
        line = input()
        if line.lower() == 'exit':
            return False
        
        token_json += line
        
        # Check if we have a valid JSON
        try:
            data = json.loads(token_json)
            if all(k in data for k in ['accessToken', 'refreshToken', 'tokenExpireTime', 'uuid']):
                logger.info("Valid token information detected")
                
                # Extract only the necessary fields
                token_data = {
                    'accessToken': data['accessToken'],
                    'refreshToken': data['refreshToken'],
                    'tokenExpireTime': data['tokenExpireTime'],
                    'uuid': data['uuid']
                }
                
                # Initialize Webull instance and set token
                wb = webull()
                wb._refresh_token = token_data['refreshToken']
                wb._access_token = token_data['accessToken']
                wb._token_expire = token_data['tokenExpireTime']
                wb._uuid = token_data['uuid']
                
                # Try to refresh the token to verify it works
                try:
                    logger.info("Refreshing token to verify it works...")
                    refresh_result = wb.refresh_login()
                    
                    # Update token data with refreshed values
                    token_data['refreshToken'] = refresh_result['refreshToken']
                    token_data['accessToken'] = refresh_result['accessToken']
                    token_data['tokenExpireTime'] = refresh_result['tokenExpireTime']
                    
                    # Get account ID
                    account_id = wb.get_account_id()
                    if not account_id:
                        logger.warning("Could not get account ID")
                        print("Token refresh succeeded but could not get account ID.")
                        print("This may indicate a problem with the token.")
                        print("Do you want to continue anyway? (y/n): ", end="")
                        if input().lower() != 'y':
                            return False
                    
                    # Save the refreshed token
                    save_token(wb, token_data)
                    logger.info("Token refreshed and saved")
                    return wb
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    print(f"The provided token could not be refreshed: {e}")
                    print("Please try again with a new token or type 'exit' to quit.")
                    token_json = ""
                    print("> ", end="")
            else:
                # Could be partial JSON, continue reading
                continue
        except json.JSONDecodeError:
            # Not valid JSON yet, continue reading
            continue

def login_webull():
    """Log in to webull API using credentials from environment or saved token"""
    wb = webull()
    
    # Try to load saved token first
    token_loaded = load_token(wb)
    
    if token_loaded:
        # Check if token is expired
        if token_is_expired(wb._token_expire):
            logger.info("Saved token is expired or expiring soon, refreshing...")
            try:
                refresh_result = wb.refresh_login()
                
                # Verify the refresh was successful
                if 'accessToken' in refresh_result and refresh_result['accessToken']:
                    logger.info("Token refreshed successfully")
                    save_token(wb)
                    
                    # Verify the refreshed token works
                    account_id = wb.get_account_id()
                    if account_id:
                        logger.info(f"Account ID verified: {account_id}")
                        return wb
                    else:
                        logger.warning("Could not verify account ID with refreshed token")
                else:
                    logger.warning("Token refresh did not return a valid access token")
            except Exception as e:
                logger.warning(f"Error refreshing token: {e}")
                logger.info("Will try manual token setup")
        else:
            # Token not expired, verify it works
            try:
                account_id = wb.get_account_id()
                if account_id:
                    logger.info(f"Using saved token, account ID: {account_id}")
                    return wb
                else:
                    logger.warning("Saved token failed account ID verification")
            except Exception as e:
                logger.warning(f"Error verifying saved token: {e}")
    
    # Try regular login with email/password
    try:
        email = os.getenv('WEBULL_EMAIL')
        password = os.getenv('WEBULL_PASSWORD')
        
        if not email or not password:
            logger.warning("Webull email or password not found in .env file")
        else:
            logger.info(f"Attempting to login with credentials for {email}...")
            try:
                # Try login without MFA first
                result = wb.login(email, password)
                
                # Check if login succeeded
                if isinstance(result, dict) and 'accessToken' in result:
                    logger.info("Login successful!")
                    save_token(wb)
                    return wb
                else:
                    logger.warning(f"Regular login failed: {result}")
            except Exception as e:
                logger.warning(f"Exception during login: {e}")
    except Exception as e:
        logger.warning(f"Error preparing for regular login: {e}")
    
    # If we get here, try manual token setup
    logger.info("Attempting manual token setup...")
    return manual_token_setup()

def refresh_session(wb):
    """Refresh the session if needed"""
    try:
        # Check token expiration and refresh if needed
        if hasattr(wb, '_token_expire') and wb._token_expire:
            if token_is_expired(wb._token_expire):
                logger.info("Access token expiring soon, refreshing...")
                refresh_result = wb.refresh_login()
                
                # Verify the refresh was successful
                if 'accessToken' in refresh_result and refresh_result['accessToken']:
                    save_token(wb)
                    return True
    except Exception as e:
        logger.warning(f"Failed to refresh session: {e}")
    return False

def get_pnl_from_account(wb, max_retries=2):
    """
    Try multiple approaches to get P/L information from the account
    Returns a tuple of (dollar_pnl, percentage_pnl)
    """
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Refresh session if needed
            refresh_session(wb)
            
            logger.info("Getting account information...")
            
            # Try to get account data
            try:
                account = wb.get_account()
                
                # Check if response indicates token expiration
                if isinstance(account, dict) and account.get('success') is False:
                    error_code = str(account.get('code', ''))
                    error_msg = str(account.get('msg', ''))
                    
                    if 'token.expire' in error_code or 'token' in error_msg.lower():
                        if retry_count < max_retries:
                            logger.info("Token expired, refreshing...")
                            wb.refresh_login()
                            save_token(wb)
                            retry_count += 1
                            continue
                
                if not account:
                    logger.warning("Empty account data returned")
                    retry_count += 1
                    continue
                
                logger.info("Successfully got account data")
                # Save account data for debugging
                with open('account_data.json', 'w') as f:
                    json.dump(account, f, indent=2)
                
                # Try to extract P/L information
                if isinstance(account, dict) and 'unrealizedProfitLoss' in account:
                    pnl = float(account['unrealizedProfitLoss'])
                    logger.info(f"Found unrealizedProfitLoss: {pnl}")
                    
                    # Calculate percentage if possible
                    if 'accountValue' in account and float(account['accountValue']) > 0:
                        account_value = float(account['accountValue'])
                        pnl_pct = pnl / account_value
                        return pnl, pnl_pct
                    
                    # Return just the dollar value if no percentage can be calculated
                    return pnl, 0.0
                
                # Other possible field names for P/L
                for field in ['dayProfitLoss', 'totalProfitLoss', 'unrealizedProfit']:
                    if isinstance(account, dict) and field in account and account[field]:
                        try:
                            pnl = float(account[field])
                            logger.info(f"Found {field}: {pnl}")
                            return pnl, 0.0  # Return without percentage
                        except (ValueError, TypeError):
                            pass
            except Exception as e:
                logger.warning(f"Could not get account data: {e}")
            
            # Try to get positions and calculate P/L if account method didn't work
            try:
                logger.info("Getting positions...")
                positions = wb.get_positions()
                
                # Save positions data for debugging
                with open('positions_data.json', 'w') as f:
                    json.dump(positions, f, indent=2)
                
                if positions:
                    logger.info(f"Found {len(positions)} positions")
                    
                    total_current_value = 0.0
                    total_cost = 0.0
                    
                    for pos in positions:
                        try:
                            market_value = float(pos.get('marketValue', 0))
                            cost_basis = float(pos.get('costBasis', 0))
                            if cost_basis == 0:
                                # Try alternative fields
                                cost_price = float(pos.get('costPrice', 0))
                                quantity = float(pos.get('quantity', 0))
                                cost_basis = cost_price * quantity
                                
                            total_current_value += market_value
                            total_cost += cost_basis
                        except (ValueError, TypeError, KeyError) as e:
                            logger.warning(f"Error processing position: {e}")
                    
                    if total_cost > 0:
                        pnl = total_current_value - total_cost
                        pnl_pct = pnl / total_cost
                        logger.info(f"Calculated P/L from positions: ${pnl:.2f} ({pnl_pct:.2%})")
                        return pnl, pnl_pct
            except Exception as e:
                logger.warning(f"Could not get positions: {e}")
            
            # If we got here and have retries left, try again
            if retry_count < max_retries:
                retry_count += 1
                logger.info(f"Retrying P/L retrieval (attempt {retry_count+1}/{max_retries+1})...")
                time.sleep(2)  # Short delay before retry
                continue
            else:
                # Out of retries
                break
                
        except Exception as e:
            logger.error(f"Error getting P/L: {e}")
            if retry_count < max_retries:
                retry_count += 1
                logger.info(f"Retrying P/L retrieval (attempt {retry_count+1}/{max_retries+1})...")
                time.sleep(2)  # Short delay before retry
                continue
            else:
                break
    
    logger.warning("Could not determine P/L from API after retries")
    return 0.0, 0.0

def format_pnl(dollar_pnl, pct_pnl):
    """Format P/L values for display"""
    return f"${dollar_pnl:.2f} ({pct_pnl:.2%})"

def format_account_info(dollar_pnl, pct_pnl, cash_balance, account_value):
    """Format account information for display"""
    pnl_str = f"P/L: ${dollar_pnl:.2f} ({pct_pnl:.2%})"
    balance_str = f"Cash: ${cash_balance:.2f} | Account Value: ${account_value:.2f}"
    return f"{pnl_str} | {balance_str}"

def check_threshold(dollar_pnl, pct_pnl):
    """Check if P/L has reached the threshold based on threshold type"""
    if THRESHOLD_TYPE == 'DOLLAR':
        # For dollar threshold, compare actual dollar amount
        return dollar_pnl <= THRESHOLD
    else:
        # For percentage threshold, compare percentage
        return pct_pnl <= THRESHOLD

def get_futures_data_with_token(access_token, futures_account_id):
    """Get futures account data using curl with just an access token"""
    try:
        import subprocess
        import json
        import uuid
        import time
        
        # Get headers from global dictionary
        headers = WEBULL_HEADERS
        
        # Using the exact headers from the working curl command
        curl_cmd = [
            'curl', '-s',
            f'https://ustrade.webullfinance.com/api/trading/v1/webull/asset/future/summary?secAccountId={futures_account_id}',
            '-H', 'accept: */*',
            '-H', 'accept-language: en-US,en;q=0.9',
            '-H', f'access_token: {access_token}',
            '-H', 'app: global',
            '-H', 'app-group: broker',
            '-H', 'appid: wb_web_us',
            '-H', 'device-type: Web',
            '-H', f'did: {headers["did"]}',
            '-H', 'hl: en',
            '-H', 'lzone: dc_core_r002',
            '-H', 'origin: https://www.webull.com',
            '-H', 'os: web',
            '-H', f'osv: {headers["osv"]}',
            '-H', 'platform: web',
            '-H', f'referer: {headers["referer"]}',
            '-H', f'reqid: {uuid.uuid4().hex.lower()}',
            '-H', f't_time: {int(time.time() * 1000)}',
            '-H', f't_token: {headers["t_token"]}',
            '-H', f'user-agent: {headers["user_agent"]}',
            '-H', 'ver: 1.0.0',
            '-H', f'x-s: {headers["x_s"]}',
            '-H', f'x-sv: {headers["x_sv"]}'
        ]
        
        # Log the constructed command for debugging (excluding sensitive parts)
        logger.info(f"Executing curl to get futures data for account {futures_account_id}")
        
        # Execute the curl command
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                
                # Check for token expiration
                if 'code' in data and 'trade.token.expire' in data['code']:
                    logger.warning("Token expired during curl request")
                    return {'tokenExpired': True}
                
                # Save response for debugging
                with open(f'futures_data_{futures_account_id}.json', 'w') as f:
                    json.dump(data, f, indent=2)
                    
                logger.info(f"Successfully retrieved futures data via curl")
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing futures API response: {e}")
                logger.debug(f"Raw response: {result.stdout[:100]}...")
                return None
        else:
            logger.warning(f"Curl command failed: {result.returncode}")
            if result.stderr:
                logger.warning(f"Stderr: {result.stderr}")
            return None
            
    except Exception as e:
        logger.warning(f"Error getting futures data with curl: {e}")
        return None

def send_notification(title, message, sound=True):
    """
    Send a system notification with optional sound
    """
    try:
        # Check if we're on macOS
        if sys.platform == 'darwin':
            # Use osascript to send notification with sound
            sound_param = "with sound" if sound else "without sound"
            cmd = [
                'osascript', 
                '-e', 
                f'display notification "{message}" with title "{title}" {sound_param}'
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"Sent notification: {title} - {message}")
            return True
        # Add support for Linux
        elif sys.platform.startswith('linux'):
            # Check if notify-send is available
            try:
                sound_cmd = []
                if sound:
                    # Play a sound using paplay if available
                    sound_cmd = ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"]
                    subprocess.run(["which", "paplay"], check=True, stdout=subprocess.PIPE)
                
                # Send notification
                subprocess.run(["notify-send", title, message], check=True)
                
                # Play sound if enabled
                if sound and sound_cmd:
                    subprocess.run(sound_cmd, check=True)
                
                logger.info(f"Sent notification: {title} - {message}")
                return True
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("Could not send notification on Linux - notification tools not available")
                return False
        else:
            logger.warning(f"Notifications not supported on platform: {sys.platform}")
            return False
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

def main():
    # Load Webull configuration headers
    load_webull_configs()

    threshold_type_str = "Dollar" if THRESHOLD_TYPE == 'DOLLAR' else "Percentage"
    threshold_display = f"${THRESHOLD:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{THRESHOLD:.2%}"
    
    logger.info(f"Starting Webull P/L monitor with {threshold_type_str} threshold: {threshold_display}")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"Kill script: {SCRIPT_PATH}")
    
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    try:
        # First, try to load the saved access token and see if direct API access works
        access_token = None
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                access_token = token_data.get('accessToken')
                logger.info(f"Loaded access token: {access_token[:10]}...{access_token[-5:]}")
            except Exception as e:
                logger.warning(f"Error loading token: {e}")
                send_notification("Webull Monitor Warning", "Error loading token file")
        
        # Test direct API access with the token
        if access_token:
            futures_account_id = os.getenv('FUTURES_ACCOUNT_ID', '23620627')
            logger.info(f"Testing direct API access with saved token for account {futures_account_id}")
            data = get_futures_data_with_token(access_token, futures_account_id)
            
            if data and 'capital' in data:
                logger.info("Direct API access with saved token successful!")
                # Initialize a webull object just to store the token
                wb = webull()
                wb._access_token = access_token
            else:
                logger.warning("Direct API access with saved token failed, attempting login")
                send_notification("Webull Monitor Warning", "Direct API access failed, attempting normal login")
                wb = login_webull()
        else:
            logger.info("No access token found, attempting login")
            wb = login_webull()
            
        if not wb:
            logger.error("Failed to authenticate, exiting")
            send_notification("Webull Monitor Error", "Failed to authenticate with Webull", True)
            return
            
        logger.info("Successfully authenticated with Webull")
        send_notification("Webull Monitor", "Successfully connected to Webull account", False)
        
        # Main monitoring loop
        while True:
            try:
                # Try to get data directly using curl with all required headers first
                try:
                    futures_account_id = os.getenv('FUTURES_ACCOUNT_ID', '23620627')
                    data = get_futures_data_with_token(wb._access_token, futures_account_id)
                    
                    if data and 'capital' in data:
                        capital = data['capital']
                        
                        # Extract P/L
                        pnl = 0.0
                        if 'unrealizedProfitLoss' in capital:
                            pnl = float(capital['unrealizedProfitLoss'])
                            logger.info(f"Found futures unrealizedProfitLoss: {pnl}")
                            
                        # Extract account value
                        account_value = 0.0
                        if 'netLiquidationValue' in capital:
                            account_value = float(capital['netLiquidationValue'])
                            logger.info(f"Found futures netLiquidationValue: {account_value}")
                        
                        # Extract cash balance
                        cash_balance = 0.0
                        if 'totalCashValue' in capital:
                            cash_balance = float(capital['totalCashValue'])
                            logger.info(f"Found futures totalCashValue: {cash_balance}")
                        
                        # Calculate percentage if possible
                        pct_pnl = 0.0
                        if account_value > 0:
                            pct_pnl = pnl / account_value
                        
                        # Additional balance information
                        if 'futureBuyingPower' in capital:
                            buying_power = float(capital['futureBuyingPower'])
                            logger.info(f"Futures buying power: ${buying_power:.2f}")
                            
                        # Check risk status
                        if 'riskStatus' in data:
                            risk_status = data['riskStatus']
                            logger.info(f"Account risk status: {risk_status}")
                            
                        # Log the formatted info
                        logger.info(format_account_info(pnl, pct_pnl, cash_balance, account_value))
                        
                        # Check threshold
                        if check_threshold(pnl, pct_pnl):
                            threshold_display = f"${THRESHOLD:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{THRESHOLD:.2%}"
                            current_display = f"${pnl:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{pct_pnl:.2%}"
                            
                            logger.warning(f"P/L threshold reached: {current_display} <= {threshold_display}")
                            
                            # Send notification that threshold was reached
                            notification_message = f"P/L threshold reached: {current_display} <= {threshold_display}"
                            send_notification("Webull P/L Alert", notification_message, True)
                            
                            if trigger_kill():
                                logger.info("Kill switch activated successfully")
                                send_notification("Webull Kill Switch", "Kill switch activated successfully", True)
                                break
                            else:
                                logger.error("Failed to activate kill switch, will retry")
                                send_notification("Webull Kill Switch Error", "Failed to activate kill switch", True)
                    else:
                        logger.warning("Direct API access failed, falling back to Webull API methods")
                        # Send notification about connection issue
                        send_notification("Webull Connection Error", "Failed to get account data", True)
                        
                        # Check if token expired
                        if data and isinstance(data, dict) and 'tokenExpired' in data and data['tokenExpired']:
                            logger.warning("Token expired, need new token")
                            send_notification("Webull Token Expired", "Login token has expired", True)
                            wb = login_webull()
                            if not wb:
                                logger.error("Failed to get new token, exiting")
                                send_notification("Webull Error", "Failed to get new token", True)
                                return
                        
                        # Fall back to standard method
                        dollar_pnl, pct_pnl, cash_balance, account_value = get_pnl_from_account(wb)
                        logger.info(format_account_info(dollar_pnl, pct_pnl, cash_balance, account_value))
                        
                        # Check threshold with fallback values
                        if check_threshold(dollar_pnl, pct_pnl):
                            threshold_display = f"${THRESHOLD:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{THRESHOLD:.2%}"
                            current_display = f"${dollar_pnl:.2f}" if THRESHOLD_TYPE == 'DOLLAR' else f"{pct_pnl:.2%}"
                            
                            logger.warning(f"P/L threshold reached: {current_display} <= {threshold_display}")
                            
                            # Send notification that threshold was reached
                            notification_message = f"P/L threshold reached: {current_display} <= {threshold_display}"
                            send_notification("Webull P/L Alert", notification_message, True)
                            
                            if trigger_kill():
                                logger.info("Kill switch activated successfully")
                                send_notification("Webull Kill Switch", "Kill switch activated successfully", True)
                                break
                            else:
                                logger.error("Failed to activate kill switch, will retry")
                                send_notification("Webull Kill Switch Error", "Failed to activate kill switch", True)
                except Exception as e:
                    logger.error(f"Error during direct API access: {e}")
                    send_notification("Webull API Error", f"Error accessing Webull API: {str(e)[:50]}", True)
                    
                    # Fall back to standard method
                    dollar_pnl, pct_pnl, cash_balance, account_value = get_pnl_from_account(wb)
                    logger.info(format_account_info(dollar_pnl, pct_pnl, cash_balance, account_value))
                
                # Reset error counter on successful API call
                consecutive_errors = 0
            
            except Exception as e:
                logger.error(f"Error during monitoring cycle: {e}")
                consecutive_errors += 1
                
                if consecutive_errors == 1:
                    # Send notification on first error
                    send_notification("Webull Monitor Error", f"Error during monitoring: {str(e)[:50]}", True)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.warning(f"Too many consecutive errors ({consecutive_errors}), attempting to reconnect...")
                    send_notification("Webull Connection Lost", "Attempting to reconnect to Webull", True)
                    
                    try:
                        wb = login_webull()
                        if wb:
                            logger.info("Successfully reconnected to Webull")
                            send_notification("Webull Reconnected", "Successfully reconnected to Webull", True)
                            consecutive_errors = 0
                        else:
                            logger.error("Failed to reconnect, exiting")
                            send_notification("Webull Error", "Failed to reconnect to Webull", True)
                            return
                    except Exception as reconnect_error:
                        logger.error(f"Failed to reconnect: {reconnect_error}")
                        send_notification("Webull Error", f"Fatal connection error: {str(reconnect_error)[:50]}", True)
                        return
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        send_notification("Webull Monitor", "Monitor stopped by user", False)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        send_notification("Webull Monitor Critical Error", f"Unexpected error: {str(e)[:50]}", True)
        raise

if __name__ == "__main__":
    main()
