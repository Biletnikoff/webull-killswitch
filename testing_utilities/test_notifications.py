#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

def send_notification(title, message, sound=True):
    """
    Send a system notification with optional sound using terminal-notifier
    """
    try:
        # Check if we're on macOS
        if sys.platform == 'darwin':
            # Use terminal-notifier from Homebrew for reliable notifications
            try:
                # Format the message to ensure it's visible
                # Add alert icon for important notifications
                if "alert" in title.lower() or "error" in title.lower() or "kill" in title.lower() or "p/l" in title.lower():
                    cmd = [
                        "terminal-notifier",
                        "-title", title,
                        "-subtitle", "Webull Monitor",
                        "-message", message,
                        "-contentImage", "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertStopIcon.icns",
                        "-sound", "Glass"
                    ]
                else:
                    cmd = [
                        "terminal-notifier",
                        "-title", title,
                        "-subtitle", "Webull Monitor",
                        "-message", message
                    ]
                    # Only add sound for non-alerts if sound is enabled
                    if sound:
                        cmd.extend(["-sound", "Glass"])
                
                # Execute the notification command
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"Notification sent via terminal-notifier: {title} - {message}")
                return True
                
            except Exception as e:
                logger.warning(f"Terminal-notifier failed: {e}")
                
                # Fall back to playing sound directly
                if sound:
                    try:
                        sound_file = '/System/Library/Sounds/Glass.aiff'
                        if os.path.exists(sound_file):
                            subprocess.run(['afplay', sound_file], check=True)
                            logger.info("Played sound directly with afplay as fallback")
                    except Exception as sound_e:
                        logger.warning(f"Failed to play sound: {sound_e}")
                
                # Log the failure but don't return False yet
                logger.info(f"Notification attempted (may not be visible): {title} - {message}")
                return False
                
        # For Linux platforms
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

def trigger_kill():
    """
    Trigger the kill script to close trading applications
    Returns True if successful, False otherwise
    """
    # Get the path to the kill script
    kill_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "killTradingApp.scpt")
    
    # Check if kill script exists
    if not os.path.exists(kill_script_path):
        logger.error(f"Kill script not found at {kill_script_path}")
        send_notification("Kill Switch Error", "Kill script not found!")
        return False
    
    # Execute the kill script
    logger.info(f"Executing kill script: {kill_script_path}")
    try:
        result = subprocess.run(
            ["osascript", kill_script_path],
            check=False,
            capture_output=True,
            text=True
        )
        
        # Log the script output
        print("\nKill script output:")
        print("=" * 50)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"ERROR: {result.stderr}")
        print("=" * 50)
        
        logger.info("Kill script execution complete - check log above for details")
        
        # Check if script executed successfully
        if result.returncode == 0:
            logger.info("Kill switch triggered successfully")
            send_notification("Kill Switch Test", "Kill switch triggered successfully")
            return True
        else:
            logger.error(f"Kill script failed with return code {result.returncode}")
            send_notification("Kill Switch Error", f"Kill script failed with code {result.returncode}")
            return False
    
    except Exception as e:
        logger.error(f"Error executing kill script: {e}")
        send_notification("Kill Switch Error", f"Error executing kill script: {e}")
        return False

def test_notifications():
    """Test different types of notifications"""
    logger.info("Testing notifications...")
    
    # Test notification without sound
    send_notification("Test Notification", "This is a test notification without sound", False)
    logger.info("Sent notification without sound. Did you see it?")
    time.sleep(2)
    
    # Test notification with sound
    send_notification("Test Notification with Sound", "This notification should play a sound", True)
    logger.info("Sent notification with sound. Did you hear the sound?")
    time.sleep(2)
    
    # Test P/L threshold notification
    send_notification("Webull P/L Alert", "P/L threshold reached: $-600.00 <= $-500.00", True)
    logger.info("Sent P/L threshold notification with sound")
    time.sleep(2)
    
    # Test kill switch activated notification
    send_notification("Kill Switch Activated", "Kill switch has been triggered due to P/L threshold", True)
    logger.info("Sent kill switch notification with sound")
    time.sleep(2)
    
    # Test error notifications
    send_notification("Webull Connection Error", "Failed to get account data", True)
    logger.info("Sent connection error notification with sound")
    time.sleep(2)
    
    send_notification("Webull Token Expired", "Login token has expired", True)
    logger.info("Sent token expiration notification with sound")
    time.sleep(2)
    
    send_notification("Webull Monitor Error", "Error during monitoring: Connection timeout", True)
    logger.info("Sent monitoring error notification with sound")
    time.sleep(2)
    
    # Test detailed P/L notification
    pnl = -600.00
    account_value = 10000.00
    pct_pnl = pnl / account_value
    cash_balance = 2500.00
    formatted_pnl = f"P/L: ${pnl:.2f} ({pct_pnl:.2%})"
    formatted_balance = f"Cash: ${cash_balance:.2f} | Account Value: ${account_value:.2f}"
    detailed_message = f"{formatted_pnl} | {formatted_balance}"
    
    send_notification("Webull Account Update", detailed_message, True)
    logger.info("Sent detailed account notification with sound")

def simulate_monitor_run():
    """Simulate a monitor run with notifications"""
    logger.info("Simulating monitor run with notifications...")
    
    # Simulate connecting to Webull
    send_notification("Webull Monitor", "Successfully connected to Webull account")
    logger.info("Connected to Webull account")
    
    # Simulate getting account data
    account_data = {
        "p_l": -100.0,
        "p_l_percent": -1.0,
        "cash": 2500.0,
        "account_value": 10000.0
    }
    
    # Simulate monitoring loop
    for i in range(3):
        if i == 1:
            account_data["p_l"] = -300.0
            account_data["p_l_percent"] = -3.0
        elif i == 2:
            account_data["p_l"] = -600.0
            account_data["p_l_percent"] = -6.0
        
        # Log account data
        logger.info(f"P/L: ${account_data['p_l']:.2f} ({account_data['p_l_percent']:.2f}%) | Cash: ${account_data['cash']:.2f} | Account Value: ${account_data['account_value']:.2f}")
        
        # Check if threshold reached
        if account_data["p_l"] <= -500.0:
            # Send P/L alert notification
            send_notification("Webull P/L Alert", f"P/L threshold reached: ${account_data['p_l']:.2f} <= $-500.00")
            logger.info("P/L threshold reached, sending alert notification")
            
            # Prompt for kill switch
            print("\nP/L threshold of $-500.00 has been reached with P/L of ${:.2f}".format(account_data["p_l"]))
            print("\nWARNING: Triggering the kill switch will:")
            print("1. Close all applications that start with 'Webull'")
            print("2. Close all Chrome tabs containing 'webull.com'")
            print("\nWould you like to trigger the kill switch? (y/n): ", end="")
            
            try:
                response = input().lower()
                if response == 'y':
                    test_kill_switch()
            except EOFError:
                # Handle case where input is not available (e.g., when piping commands)
                logger.info("Automated test mode detected - automatically triggering kill switch")
                test_kill_switch()
            
            # Break after triggering kill switch
            break
        
        # Wait a bit before next check
        time.sleep(3)

def test_kill_switch():
    """Test the kill switch functionality"""
    logger.info("Testing kill switch...")
    
    print("\nWARNING: This will attempt to:")
    print("1. Close all applications that start with 'Webull'")
    print("2. Close all Chrome tabs containing 'webull.com'")
    print("\nMake sure you have the killTradingApp.scpt file in the same directory.")
    print("Proceed? (y/n): ", end="")
    
    try:
        response = input().lower()
        if response != 'y':
            logger.info("Kill switch test cancelled")
            return False
    except EOFError:
        # Handle case where input is not available (e.g., when piping commands)
        logger.info("Automated test mode detected - proceeding with kill switch test")
    
    # Send pre-kill notification
    send_notification("Kill Switch Test", "About to test kill switch in 3 seconds...")
    time.sleep(3)
    
    # Trigger kill script
    return trigger_kill()

def main():
    """Main test function"""
    print("Webull Monitor Test Utility")
    print("==========================\n")
    print("1. Test Basic Notifications")
    print("2. Test Kill Switch")
    print("3. Simulate Monitor Run")
    print("4. Run All Tests")
    print("5. Exit\n")
    
    choice = input("Enter your choice (1-5): ")
    
    if choice == '1':
        test_notifications()
    elif choice == '2':
        test_kill_switch()
    elif choice == '3':
        simulate_monitor_run()
    elif choice == '4':
        test_notifications()
        time.sleep(2)
        test_kill_switch()
        time.sleep(2)
        simulate_monitor_run()
    elif choice == '5':
        print("Exiting...")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 