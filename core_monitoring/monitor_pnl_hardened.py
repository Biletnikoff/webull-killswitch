#!/usr/bin/env python3
"""
Hardened Webull Monitor Script - Designed to be extremely difficult to terminate.
This script will continue monitoring your Webull account's P/L and execute the kill switch
when necessary, ignoring most attempts to terminate it.
"""
import os
import sys
import subprocess
import time
import logging
import signal
import atexit
import argparse
from datetime import datetime, time as dt_time, timedelta
import pytz
import requests
import json

# Add parent directory to path to allow imports from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import modules from other directories
from installation_maintenance.make_unkillable import make_process_unkillable
from authentication.webull_auth import refresh_auth, get_auth_headers, WebullAuth
from core_monitoring.kill_switch import execute_kill_switch as execute_kill_action

# Check if webull_auth module is available
WEBULL_AUTH_AVAILABLE = True

# Configuration - these can be moved to an env file
PNL_THRESHOLD = -650  # Trigger kill switch when P/L drops below this value
CHECK_INTERVAL = 60     # Check P/L every this many seconds

# Webull API configuration
WEBULL_API_BASE = "https://userapi.webull.com/api"
ACCOUNT_ENDPOINT = f"{WEBULL_API_BASE}/account/getSecAccountList"
PNL_ENDPOINT = f"{WEBULL_API_BASE}/account/getAccountV5"

# Configure logging
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")
os.makedirs(log_dir, exist_ok=True)  # Ensure log directory exists
log_file = os.path.join(log_dir, "monitor_hardened.log")

# Force clear any existing handlers to avoid duplicates
logging.getLogger().handlers = []

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),  # Append mode
        logging.StreamHandler(sys.stdout)  # Log to stdout
    ]
)
logger = logging.getLogger()

# Force a log entry to ensure system is working
logger.info("==== LOGGING INITIALIZED ====")
logger.info(f"Log file path: {log_file}")
logger.info(f"Python version: {sys.version}")

# Print startup banner to make it more visible
print("\n" + "="*80)
print("   WEBULL KILL SWITCH MONITOR STARTING   ".center(80, '*'))
print("="*80 + "\n")

# Add this global variable at the top of the file
# Global variable to store command line arguments
global_args = None

def send_notification(title, message, sound=True):
    """Send a notification with optional sound"""
    try:
        if sys.platform == 'darwin':
            # Use terminal-notifier for better visibility
            try:
                cmd = [
                    "terminal-notifier",
                    "-title", title,
                    "-subtitle", "Webull Monitor",
                    "-message", message,
                    "-contentImage", "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertStopIcon.icns",
                    "-sound", "Glass"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"Notification sent: {title} - {message}")
                return True
            except Exception as e:
                logger.warning(f"Failed to send notification using terminal-notifier: {e}")
                try:
                    # Try to play sound directly
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], check=True)
                except:
                    pass
                return False
        return False
    except Exception as e:
        logger.error(f"Error in send_notification: {e}")
        return False

def execute_kill_switch(current_pnl=None, current_balance=None):
    """Execute the kill switch script"""
    try:
        logger.info("EXECUTING KILL SWITCH - P/L threshold reached!")
        
        # Prepare notification message
        message = f"P/L threshold reached: <= ${PNL_THRESHOLD:.2f}"
        if current_pnl is not None:
            message = f"P/L threshold reached: ${current_pnl:.2f} <= ${PNL_THRESHOLD:.2f}"
        
        # Add balance information if available
        if current_balance is not None:
            message += f"\nAccount Balance: ${current_balance:.2f}"
            # Calculate percentage if possible
            if current_balance != 0 and current_pnl is not None:
                pnl_percent = (current_pnl / current_balance) * 100
                message += f"\nP/L%: {pnl_percent:.2f}%"
        
        # Send notification
        send_notification("KILL SWITCH ACTIVATED", message)
        
        # Use the imported kill switch function
        result = execute_kill_action(current_pnl, current_balance)
        
        if result:
            logger.info("Kill switch executed successfully")
            send_notification("Kill Switch Success", "Webull applications have been terminated")
            return True
        else:
            logger.error("Kill switch execution failed")
            send_notification("Kill Switch Error", "Failed to terminate Webull applications")
            return False
    except Exception as e:
        logger.error(f"Error executing kill switch: {e}")
        send_notification("Kill Switch Error", f"Error: {str(e)}")
        return False

def simulate_get_pnl():
    """
    Simulate getting P/L from Webull API
    In a real implementation, this would connect to the Webull API
    """
    # This is just a placeholder - implement real API connection here
    # For testing, just return a value that will trigger the kill switch after a few iterations
    current_time = time.time()
    
    # Start with -100 and gradually decrease to trigger the kill switch
    cycle = int((current_time % 300) / 60)  # 0-4 based on the minute
    
    if cycle == 0:
        return -100.0
    elif cycle == 1:
        return -300.0
    elif cycle == 2:
        return -400.0
    elif cycle == 3:
        return -550.0  # This should trigger the kill switch
    else:
        return -600.0

def refresh_auth_token():
    """Refresh the authentication token"""
    try:
        logger.info("Refreshing authentication token")
        auth = WebullAuth()
        
        # If in test mode, we use test mode in the auth module
        if global_args and global_args.test:
            logger.info("Test mode: Using test mode for token refresh")
            auth.set_test_mode(True)
            success = auth.refresh_auth_token()
            
            if success:
                logger.info("Test mode: Authentication token refreshed successfully")
                return True
            else:
                logger.warning("Test mode: Failed to refresh authentication token through standard refresh")
                # In test mode, simulate success even if refresh fails
                logger.info("Test mode: Simulating successful token refresh")
                return True
                
        else:
            # Production mode - try refreshing with real token
            logger.info("Production mode: Attempting to refresh authentication token")
            success = auth.refresh_auth_token()
            
            if success:
                logger.info("Authentication token refreshed successfully")
                return True
            else:
                # Token refresh failed through normal channel, try to extract from Webull
                logger.warning("Failed to refresh token through standard refresh, attempting to extract from Webull")
                
                # Try to extract token from Webull cookies or storage
                if auth.extract_token_from_webull():
                    logger.info("Successfully extracted and updated token from Webull")
                    return True
                else:
                    # If that fails too, notify the user
                    logger.error("Failed to refresh authentication token and could not extract from Webull")
                    message = """
TOKEN REFRESH FAILED: Your Webull authentication token has expired and could not be refreshed.

Please run:
    python3 update_token.py

You will need to log in to Webull in your browser and copy token information to update your token.
Or run the monitor with --test mode until you can update your token.
"""
                    logger.error(message)
                    send_notification("Token Refresh Failed", "Authentication token expired. Please run update_token.py to update manually.")
                    return False
    except Exception as e:
        logger.error(f"Error refreshing authentication token: {e}")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Monitor Webull account P/L and execute kill switch if threshold is reached.')
    parser.add_argument('--test', action='store_true', help='Run in test mode (bypass market hours check, shorter interval)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--threshold', type=float, help='P/L threshold to trigger kill switch (negative value)', default=None)
    parser.add_argument('--interval', type=int, help='Checking interval in seconds', default=None)
    parser.add_argument('--test-pnl', type=float, help='Test P/L value to use in test mode', default=None)
    parser.add_argument('--balance-only', action='store_true', help='Only check and display the account balance without running the monitor')
    
    args = parser.parse_args()
    
    # Store args in global variable
    global global_args
    global_args = args
    
    return args

def get_account_pnl():
    """Get the current P/L from Webull API"""
    # In test mode, attempt to use the real API first but fallback to simulation if it fails
    if global_args.test:
        logger.info("Test mode enabled")
        if not hasattr(get_account_pnl, 'counter'):
            get_account_pnl.counter = 0
        else:
            get_account_pnl.counter += 1

        # Check if token is still valid
        auth = WebullAuth()
        if not auth.is_token_valid():
            logger.info("Refreshing authentication token")
            auth.refresh_auth_token()
            
        # Try real API first if we're in test mode
        try:
            logger.info("Test mode with real token: Attempting to use real API first")
            # Get account P/L from Webull API
            headers = auth.get_auth_headers()
            
            # Use proper futures endpoint from the API
            url = "https://ustrade.webullfinance.com/api/trading/v1/webull/asset/future/summary"
            
            # Add account ID parameter
            params = {"secAccountId": auth.token_data.get("user_id")}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                # Parse the response JSON
                data = response.json()
                
                # Extract the P/L value from the response
                if "capital" in data and "unrealizedProfitLoss" in data["capital"]:
                    pnl = float(data["capital"]["unrealizedProfitLoss"])
                    logger.info(f"API Success! Current P/L from real API: ${pnl:.2f}")
                    return pnl
                else:
                    logger.warning(f"Could not find P/L in API response, falling back to simulation")
            else:
                if response.status_code == 403:
                    error_msg = f"Authentication failed with status 403. Token has expired or is invalid."
                    logger.error(error_msg)
                    
                    # Send notification about token expiration - ALWAYS do this, don't silently fail
                    send_notification(
                        "Webull Auth Failed", 
                        "Your authentication token has expired. Run update_token.py to generate a new one.", 
                        True
                    )
                    
                    # Write a clear error message to the log that the watchdog can detect
                    logger.error("Token refresh failed with status 403")
                
                logger.warning(f"API call failed with status {response.status_code}, falling back to simulation")
        except Exception as e:
            logger.warning(f"Error using real API: {str(e)}, falling back to simulation")
        
        # Fallback to simulation
        logger.info("Test mode: Simulating PNL API response")
        
        # Use test value if provided, otherwise simulate some P/L based on cycle
        if global_args.test_pnl is not None:
            test_pnl = global_args.test_pnl
            logger.info(f"Using test P/L value: ${test_pnl:.2f}")
            return float(test_pnl)
        
        # Create a varying P/L for testing
        base_pnl = -300
        # Add some variation for testing (cycle between -300 and -400)
        if get_account_pnl.counter % 15 >= 10:
            test_pnl = base_pnl - 100  # Decrease P/L
        else:
            test_pnl = base_pnl

        # On cycle 20, trigger a threshold breach for testing
        if get_account_pnl.counter == 20:
            test_pnl = -550  # Should trigger kill switch if threshold is -500
            
        logger.info(f"Using test P/L value: ${test_pnl:.2f}")
        return float(test_pnl)

    # For non-test mode, just use the real API
    try:
        # Get account P/L from Webull API
        auth = WebullAuth()
        headers = auth.get_auth_headers()
        
        # Use proper futures endpoint from the API
        url = "https://ustrade.webullfinance.com/api/trading/v1/webull/asset/future/summary"
        
        # Add account ID parameter
        params = {"secAccountId": auth.token_data.get("user_id")}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to get account P/L. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
        
        # Parse the response JSON
        data = response.json()
        
        # Extract the P/L value from the response
        if "capital" in data and "unrealizedProfitLoss" in data["capital"]:
            pnl = float(data["capital"]["unrealizedProfitLoss"])
            logger.info(f"Current P/L: ${pnl:.2f}")
            return pnl
        
        logger.error(f"Could not find P/L in API response: {data}")
        return None
    except Exception as e:
        logger.error(f"Error getting account P/L: {str(e)}")
        return None

def get_account_balance():
    """Get the current account balance from Webull API"""
    # In test mode, attempt to use the real API first but fallback to simulation if it fails
    if global_args.test:
        logger.info("Test mode enabled for balance check")
        
        # Check if token is still valid
        auth = WebullAuth()
        if not auth.is_token_valid():
            logger.info("Refreshing authentication token for balance check")
            auth.refresh_auth_token()
            
        # Try real API first if we're in test mode
        try:
            logger.info("Test mode with real token: Attempting to get real balance")
            # Get account balance from Webull API
            headers = auth.get_auth_headers()
            
            # Use proper futures endpoint from the API
            url = "https://ustrade.webullfinance.com/api/trading/v1/webull/asset/future/summary"
            
            # Add account ID parameter
            params = {"secAccountId": auth.token_data.get("user_id")}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                # Parse the response JSON
                data = response.json()
                
                # Extract the balance value from the response - multiple options for different types of accounts
                if "capital" in data:
                    capital = data["capital"]
                    # Prefer totalCashValue for cash balance
                    if "totalCashValue" in capital:
                        balance = float(capital["totalCashValue"])
                        logger.info(f"API Success! Current cash balance from real API: ${balance:.2f}")
                        return balance
                    # Or try netLiquidationValue for total account value
                    elif "netLiquidationValue" in capital:
                        balance = float(capital["netLiquidationValue"])
                        logger.info(f"API Success! Current net liquidation value from real API: ${balance:.2f}")
                        return balance
                    # Fallback to futureBuyingPower
                    elif "futureBuyingPower" in capital:
                        balance = float(capital["futureBuyingPower"])
                        logger.info(f"API Success! Current futures buying power from real API: ${balance:.2f}")
                        return balance
                    else:
                        logger.warning(f"Could not find balance fields in API response, falling back to simulation")
                else:
                    logger.warning(f"Could not find capital data in API response, falling back to simulation")
            else:
                if response.status_code == 403:
                    error_msg = f"Authentication failed with status 403. Token has expired or is invalid."
                    logger.error(error_msg)
                    
                    # Send notification about token expiration - ALWAYS do this, don't silently fail
                    send_notification(
                        "Webull Auth Failed", 
                        "Your authentication token has expired. Run update_token.py to generate a new one.", 
                        True
                    )
                    
                    # Write a clear error message to the log that the watchdog can detect
                    logger.error("Token refresh failed with status 403")
                
                logger.warning(f"API call failed with status {response.status_code}, falling back to simulation")
        except Exception as e:
            logger.warning(f"Error getting real balance: {str(e)}, falling back to simulation")
        
        # Fallback to simulation
        logger.info("Test mode: Simulating balance API response")
        
        # Simulate a balance value
        test_balance = 10000.00
        logger.info(f"Using test balance value: ${test_balance:.2f}")
        return float(test_balance)

    # For non-test mode, just use the real API
    try:
        # Get account balance from Webull API
        auth = WebullAuth()
        headers = auth.get_auth_headers()
        
        # Use proper futures endpoint from the API
        url = "https://ustrade.webullfinance.com/api/trading/v1/webull/asset/future/summary"
        
        # Add account ID parameter
        params = {"secAccountId": auth.token_data.get("user_id")}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to get account balance. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
        
        # Parse the response JSON
        data = response.json()
        
        # Extract the balance value from the response - multiple options for different types of accounts
        if "capital" in data:
            capital = data["capital"]
            # Prefer totalCashValue for cash balance
            if "totalCashValue" in capital:
                balance = float(capital["totalCashValue"])
                logger.info(f"Current cash balance: ${balance:.2f}")
                return balance
            # Or try netLiquidationValue for total account value
            elif "netLiquidationValue" in capital:
                balance = float(capital["netLiquidationValue"])
                logger.info(f"Current net liquidation value: ${balance:.2f}")
                return balance
            # Fallback to futureBuyingPower
            elif "futureBuyingPower" in capital:
                balance = float(capital["futureBuyingPower"])
                logger.info(f"Current futures buying power: ${balance:.2f}")
                return balance
            else:
                logger.error(f"Could not find balance fields in API response: {capital}")
                return None
        
        logger.error(f"Could not find capital data in API response: {data}")
        return None
    except Exception as e:
        logger.error(f"Error getting account balance: {str(e)}")
        return None

def respawn_if_killed():
    """Create a watchdog script to restart this process if it's killed."""
    watchdog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simple_watchdog.py")
    
    logging.debug(f"Using watchdog script at {watchdog_path}")
    
    # Check if the watchdog file exists
    if not os.path.exists(watchdog_path):
        logging.warning(f"Watchdog script not found at {watchdog_path}")
        logging.info("Please create the watchdog.py file with proper content")
        return
    
    # Check if watchdog is already running
    try:
        result = subprocess.run(
            ["pgrep", "-f", "simple_watchdog.py"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            watchdog_pid = result.stdout.strip()
            logging.info(f"Watchdog already running with PID {watchdog_pid}, not starting another instance")
            return
    except Exception as e:
        logging.error(f"Error checking for existing watchdog: {e}")
    
    # Make the script executable if it exists
    try:
        os.chmod(watchdog_path, 0o755)
        logging.debug("Made watchdog script executable")
    except Exception as e:
        logging.error(f"Failed to make watchdog executable: {e}")
        return
    
    # Start watchdog in the background
    logging.debug("Starting watchdog process")
    watchdog_cmd = ['python3', watchdog_path]
    
    try:
        subprocess.Popen(watchdog_cmd, start_new_session=True)
        logging.info("Watchdog process started to ensure this script stays running")
    except Exception as e:
        logging.error(f"Failed to start watchdog: {e}")

def cleanup():
    """Function to run when the script exits (which should be very difficult)"""
    logger.warning("Monitor script is exiting - this should not happen!")
    
    # Try to gracefully terminate any associated watchdog processes
    try:
        subprocess.run(["pkill", "-f", "simple_watchdog.py"], check=False)
        logger.info("Attempted to terminate associated watchdog processes")
    except Exception as e:
        logger.error(f"Failed to terminate watchdog processes: {e}")
    
    send_notification("Monitor Warning", "Webull Monitor has been terminated!", True)

def is_market_hours():
    """Check if current time is within market hours (6:30am-1:15pm PST on weekdays)"""
    try:
        # Get current time in Pacific timezone
        pacific_tz = pytz.timezone('US/Pacific')
        now = datetime.now(pacific_tz)
        
        # Check if it's a weekday (0=Monday, 6=Sunday)
        if now.weekday() >= 5:  # Saturday or Sunday
            logger.info(f"Current day is {now.strftime('%A')} - outside trading days")
            return False
        
        # Define market hours in PST
        market_open = dt_time(6, 30)  # 6:30am PST
        market_close = dt_time(13, 15)  # 1:15pm PST
        
        # Check if current time is within market hours
        current_time = now.time()
        if market_open <= current_time <= market_close:
            logger.info(f"Current time {current_time.strftime('%H:%M:%S')} is within market hours")
            return True
        else:
            logger.info(f"Current time {current_time.strftime('%H:%M:%S')} is outside market hours (6:30am-1:15pm PST)")
            return False
    except Exception as e:
        logger.error(f"Error checking market hours: {e}")
        # Default to running if there's an error (safer)
        return True

def get_time_until_market_open():
    """Get seconds until market opens"""
    try:
        pacific_tz = pytz.timezone('US/Pacific')
        now = datetime.now(pacific_tz)
        
        # If it's weekend, calculate time until Monday
        days_to_add = 0
        if now.weekday() == 5:  # Saturday
            days_to_add = 2  # Wait until Monday
        elif now.weekday() == 6:  # Sunday
            days_to_add = 1  # Wait until Monday
            
        # Calculate the next market open time
        market_open = datetime.combine(now.date(), dt_time(6, 30))
        market_open = pacific_tz.localize(market_open)
        
        # Add days if it's weekend or if we're past market hours
        if days_to_add > 0 or now.time() > dt_time(13, 15):
            if days_to_add == 0 and now.time() > dt_time(13, 15):
                # If we're past market close, go to next day
                days_to_add = 1
                # If tomorrow is Saturday, go to Monday (add 3 days)
                if now.weekday() == 4:  # Friday
                    days_to_add = 3
                    
            market_open = market_open + timedelta(days=days_to_add)
            
        # If we're before market open today
        if now.time() < dt_time(6, 30) and days_to_add == 0:
            # Use today's date with market open time
            market_open = datetime.combine(now.date(), dt_time(6, 30))
            market_open = pacific_tz.localize(market_open)
            
        # Calculate seconds until market open
        seconds_until_open = (market_open - now).total_seconds()
        
        if seconds_until_open < 0:
            # If calculation went wrong, default to short wait
            return 60
            
        return seconds_until_open
    except Exception as e:
        logger.error(f"Error calculating time until market open: {e}")
        # Default to a short wait if there's an error
        return 60

def get_time_until_market_close():
    """Get seconds until market closes if we're in market hours"""
    try:
        pacific_tz = pytz.timezone('US/Pacific')
        now = datetime.now(pacific_tz)
        
        # Calculate today's market close time
        market_close = datetime.combine(now.date(), dt_time(13, 15))
        market_close = pacific_tz.localize(market_close)
        
        # Calculate seconds until market close
        seconds_until_close = (market_close - now).total_seconds()
        
        if seconds_until_close < 0:
            # If we're already past market close
            return 0
            
        return seconds_until_close
    except Exception as e:
        logger.error(f"Error calculating time until market close: {e}")
        # Default to continuing monitoring if there's an error
        return CHECK_INTERVAL

def print_status_update(cycle_count, current_pnl=None, current_balance=None):
    """Print a status update to the console"""
    try:
        # Create a simple status line to show that we're still monitoring
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_line = f"[{now}] Kill Switch Monitor Active - Cycle: {cycle_count} | Threshold: ${PNL_THRESHOLD:.2f}"
        
        # Add P/L percentage if we can calculate it (balance is available)
        if current_pnl is not None and current_balance is not None and current_balance != 0:
            pnl_percent = (current_pnl / current_balance) * 100
            status_line += f" | P/L%: {pnl_percent:.2f}%"
        else:
            status_line += f" | P/L%: 0.00%"
        
        # Add status indicator
        status_line += f" | STATUS: ✅ Normal"
        
        print(status_line)
        
        # If we have P/L data, print that too
        if current_pnl is not None:
            status_line = f"[{now}] Kill Switch Monitor Active - Cycle: {cycle_count}"
            status_line += f" | Current P/L: ${current_pnl:.2f}"
            
            # Add balance if available
            if current_balance is not None:
                status_line += f" | Balance: ${current_balance:.2f}"
                
            status_line += f" | Threshold: ${PNL_THRESHOLD:.2f}"
            
            # Add P/L percentage if we can calculate it
            if current_balance is not None and current_balance != 0:
                pnl_percent = (current_pnl / current_balance) * 100
                status_line += f" | P/L%: {pnl_percent:.2f}%"
            else:
                status_line += f" | P/L%: 0.00%"
            
            # Add status indicator - change to warning if we're getting close to threshold
            if current_pnl <= PNL_THRESHOLD:
                status_line += f" | STATUS: ⚠️ THRESHOLD REACHED ⚠️"
            elif current_pnl <= PNL_THRESHOLD * 0.8:  # Within 80% of threshold
                status_line += f" | STATUS: ⚠️ APPROACHING THRESHOLD ⚠️"
            else:
                status_line += f" | STATUS: ✅ Normal"
                
            print(status_line)
    except Exception as e:
        logger.error(f"Error in print_status_update: {e}")

def load_env_config():
    """Load configuration from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_vars = {}
    
    if os.path.exists(env_file):
        logger.info("Loading configuration from .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
                    except ValueError:
                        continue
        return env_vars
    else:
        logger.warning(".env file not found, using defaults")
        return {}

def setup_signal_handlers():
    """Set up signal handlers for graceful termination"""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down gracefully")
        cleanup()
        sys.exit(0)
    
    # Register common termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    
    # Register cleanup to run on normal exit too
    atexit.register(cleanup)
    
    logger.debug("Signal handlers registered for graceful shutdown")

def main():
    """Main function"""
    global global_args
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor Webull account P/L and execute kill switch if threshold is reached.')
    parser.add_argument('--test', action='store_true', help='Run in test mode (bypass market hours check, shorter interval)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--threshold', type=float, help='P/L threshold to trigger kill switch (negative value)', default=None)
    parser.add_argument('--interval', type=int, help='Checking interval in seconds', default=None)
    parser.add_argument('--test-pnl', type=float, help='Test P/L value to use in test mode', default=None)
    parser.add_argument('--balance-only', action='store_true', help='Only check and display the account balance without running the monitor')
    
    global_args = parser.parse_args()
    
    # Load configuration from .env file
    env_config = load_env_config()
    
    # Make this process ignore termination signals, but only when not in test mode
    if not global_args.test:
        logger.info("Making process ignore termination signals for production mode")
        make_unkillable.make_unkillable()
    else:
        logger.info("Test mode: Not making process unkillable for easier debugging")
    
    # Update configuration from environment if not provided in command line
    if global_args.threshold is None:
        threshold_from_env = env_config.get('DEFAULT_THRESHOLD')
        if threshold_from_env:
            try:
                global_args.threshold = float(threshold_from_env)
                logger.info(f"Using threshold from .env: {global_args.threshold}")
            except ValueError:
                global_args.threshold = -300
                logger.warning(f"Invalid threshold in .env, using default: {global_args.threshold}")
        else:
            global_args.threshold = -300
            
    if global_args.interval is None:
        interval_from_env = env_config.get('CHECK_INTERVAL')
        if interval_from_env:
            try:
                global_args.interval = int(interval_from_env)
                logger.info(f"Using interval from .env: {global_args.interval}")
            except ValueError:
                global_args.interval = 60
                logger.warning(f"Invalid interval in .env, using default: {global_args.interval}")
        else:
            global_args.interval = 60
            
    if global_args.test and global_args.test_pnl is None:
        test_pnl_from_env = env_config.get('TEST_PNL')
        if test_pnl_from_env:
            try:
                global_args.test_pnl = float(test_pnl_from_env)
                logger.info(f"Using test P/L from .env: {global_args.test_pnl}")
            except ValueError:
                global_args.test_pnl = -250
                logger.warning(f"Invalid test P/L in .env, using default: {global_args.test_pnl}")
    
    # Update configuration from command line if provided
    global PNL_THRESHOLD, CHECK_INTERVAL
    if global_args.threshold:
        PNL_THRESHOLD = global_args.threshold
    if global_args.interval:
        CHECK_INTERVAL = global_args.interval
    
    # Set verbosity
    if global_args.verbose:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Special case: if --balance-only is specified, just check balance and exit
    if global_args.balance_only:
        logger.info("Balance-only mode: checking account balance")
        # Force test mode if not already set, to ensure we can get balance without valid credentials
        if not global_args.test:
            logger.info("Enabling test mode for balance check")
            global_args.test = True
        
        # Get the current account balance
        balance = get_account_balance()
        if balance is not None:
            print(f"\nCurrent Webull Account Balance: ${balance:.2f}")
            logger.info(f"Balance check completed: ${balance:.2f}")
        else:
            print("\nFailed to retrieve account balance. Check logs for details.")
            logger.error("Failed to retrieve account balance")
        
        # Exit after showing balance
        return
        
    # Register cleanup function
    atexit.register(cleanup)
    
    # Start the watchdog
    respawn_if_killed()
    
    # Send startup notification
    logger.info("==== Webull Monitor Started ====")
    logger.info(f"Monitoring P/L with threshold: ${PNL_THRESHOLD:.2f}")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info("Operating hours: 6:30am-1:15pm PST on weekdays only")
    
    if global_args.test:
        logger.info("Running in TEST MODE - market hours check will be bypassed")
    
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pid = os.getpid()
    
    notification_text = f"Started at {start_time}\nPID: {pid}\nThreshold: ${PNL_THRESHOLD:.2f}\nHours: 6:30am-1:15pm PST weekdays"
    if global_args.test:
        notification_text += "\nTEST MODE ENABLED"
    
    send_notification("Webull Monitor Started", notification_text)
    print(f"\nMonitor started at {start_time} with PID {pid}")
    print(f"Log file: {log_file}")
    
    # Initialize cycle counter
    cycle_count = 0
    
    # Main monitoring loop
    while True:
        try:
            cycle_count += 1
            
            # Print a status update
            print_status_update(cycle_count)
            
            # Check if we're within market hours (or in test mode)
            if global_args.test or is_market_hours():
                # We're in market hours or test mode, proceed with monitoring
                
                # Get the current account balance from Webull
                current_balance = get_account_balance()
                
                # Get the current P/L from Webull
                current_pnl = get_account_pnl()
                
                # Check if we got a valid P/L value
                if current_pnl is None:
                    logger.warning("Failed to get P/L data, will retry on next cycle")
                    # Use a shorter interval when retrying
                    time.sleep(min(CHECK_INTERVAL, 15))
                    continue
                
                # Log the current P/L and balance
                logger.info(f"Current P/L: ${current_pnl:.2f}")
                if current_balance:
                    logger.info(f"Current Balance: ${current_balance:.2f}")
                    if current_balance != 0:
                        pnl_percent = (current_pnl / current_balance) * 100
                        logger.info(f"P/L as percentage of balance: {pnl_percent:.2f}%")
                
                # Print a status update with P/L and balance
                print_status_update(cycle_count, current_pnl, current_balance)
                
                # Check if P/L is below threshold
                if current_pnl <= PNL_THRESHOLD:
                    logger.warning(f"P/L threshold reached: ${current_pnl:.2f} <= ${PNL_THRESHOLD:.2f}")
                    print("\n" + "!"*80)
                    print(f"THRESHOLD REACHED! P/L: ${current_pnl:.2f} <= ${PNL_THRESHOLD:.2f}")
                    print("!"*80 + "\n")
                    
                    # Execute kill switch
                    execute_kill_switch(current_pnl, current_balance)
                    
                    # Take a short break after triggering the kill switch
                    print("Taking a short break after kill switch activation...")
                    time.sleep(300)  # 5 minutes
                
                if global_args.test:
                    # In test mode, use a shorter interval
                    test_interval = min(CHECK_INTERVAL, 5)  # Using 5 seconds for better visibility
                    logger.info(f"Test mode: using shorter interval of {test_interval} seconds")
                    print(f"Waiting {test_interval} seconds before next check...")
                    time.sleep(test_interval)
                else:
                    # Get the time remaining until market close
                    remaining_time = get_time_until_market_close()
                    
                    # If we're close to market close (less than our check interval),
                    # wait until the market is closed, then calculate time until next open
                    if remaining_time < CHECK_INTERVAL:
                        logger.info(f"Market closing soon. Waiting until next market open.")
                        print(f"Market closing soon, waiting {remaining_time:.0f} seconds until close...")
                        # Wait until just past market close
                        time.sleep(remaining_time + 10)  # Add 10 seconds buffer
                        # Calculate and wait until next market open
                        sleep_time = get_time_until_market_open()
                        logger.info(f"Market closed. Sleeping for {sleep_time/60/60:.1f} hours until next market open")
                        print(f"Market closed. Sleeping for {sleep_time/60/60:.1f} hours until next market open")
                        time.sleep(sleep_time)
                    else:
                        # Wait for the next check
                        print(f"Waiting {CHECK_INTERVAL} seconds before next check...")
                        time.sleep(CHECK_INTERVAL)
            else:
                # We're outside market hours
                sleep_time = get_time_until_market_open()
                hours = sleep_time // 3600
                minutes = (sleep_time % 3600) // 60
                
                logger.info(f"Outside market hours. Sleeping for {hours:.0f} hours, {minutes:.0f} minutes until market opens")
                print(f"Outside market hours. Sleeping for {hours:.0f} hours, {minutes:.0f} minutes until market opens")
                
                # Send a notification that we're waiting for market hours
                if sleep_time > 3600:  # Only send if wait is over an hour
                    send_notification("Webull Monitor Idle", 
                                   f"Outside trading hours. Monitoring will resume at 6:30am PST on next trading day.",
                                   sound=False)
                
                # Wait until market opens, but update status every minute if in test mode
                if global_args.test:
                    # In test mode, wait for a shorter time
                    print("Test mode: sleeping for 5 seconds instead of waiting for market hours")
                    time.sleep(5)
                else:
                    # Wait until market opens (with check every 30 minutes for improved notifications)
                    remaining_sleep = sleep_time
                    while remaining_sleep > 0:
                        sleep_chunk = min(1800, remaining_sleep)  # 30 minutes or less if less than 30 minutes left
                        time.sleep(sleep_chunk)
                        remaining_sleep -= sleep_chunk
                        
                        # Send notification when 15 minutes or less remaining before market opens
                        if 0 < remaining_sleep <= 900:  # 15 minutes
                            start_time = datetime.now() + timedelta(seconds=remaining_sleep)
                            send_notification("Webull Market Opening Soon", 
                                           f"Market opens in {remaining_sleep // 60} minutes at {start_time.strftime('%H:%M')}.",
                                           sound=True)
                    
                    # Send notification when market opens
                    send_notification("Webull Monitor Active", 
                                   "Market is now open. Monitoring has resumed.",
                                   sound=True)
                    
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"ERROR: {e}")
            # Don't exit, just continue with the next iteration
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    setup_signal_handlers()
    main() 