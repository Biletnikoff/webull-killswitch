#!/usr/bin/env python3
"""
Simple Watchdog for Webull Kill Switch
Starts the monitor script with our test mode enabled
"""
import os
import sys
import subprocess
import time
import logging
import signal
import atexit

def send_notification(title, message, sound=True):
    """Send a system notification with optional sound"""
    try:
        # Check if we're on macOS
        if sys.platform == 'darwin':
            # Use terminal-notifier if available
            try:
                cmd = [
                    'terminal-notifier',
                    '-title', title,
                    '-message', message,
                    '-activate', 'com.apple.Terminal'
                ]
                
                # Add sound if enabled
                if sound:
                    cmd.extend(['-sound', 'Glass'])
                
                subprocess.run(cmd, check=True)
                print(f"Sent notification: {title} - {message}")
                return True
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to osascript
                sound_param = "with sound" if sound else "without sound"
                cmd = [
                    'osascript', 
                    '-e', 
                    f'display notification "{message}" with title "{title}" {sound_param}'
                ]
                subprocess.run(cmd, check=True)
                print(f"Sent notification: {title} - {message}")
                return True
        # Add support for Linux
        elif sys.platform.startswith('linux'):
            # Check if notify-send is available
            try:
                subprocess.run(["notify-send", title, message], check=True)
                print(f"Sent notification: {title} - {message}")
                return True
            except (subprocess.SubprocessError, FileNotFoundError):
                print("Could not send notification on Linux - notification tools not available")
                return False
        else:
            print(f"Notifications not supported on platform: {sys.platform}")
            return False
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def load_env_config():
    """Load configuration from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_vars = {}
    
    if os.path.exists(env_file):
        print("Loading configuration from .env file")
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
        print(".env file not found, using defaults")
        return {}

def check_authentication_status():
    """Check if the authentication token is valid or expired"""
    # Get directory paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Define both potential log files
    log_files = [
        os.path.join(parent_dir, "core_monitoring", "logs", "monitor_hardened.log"),
        os.path.join(parent_dir, "logs", "monitor_hardened.log")
    ]
    
    # Check both log files for authentication errors
    for log_file in log_files:
        if not os.path.exists(log_file):
            print(f"Authentication log file not found at {log_file}")
            continue  # Try the next file instead of returning None
        
        # Check last 1000 lines for auth errors (increased from 200 to catch more errors)
        try:
            print(f"Checking log file {log_file} for authentication errors")
            result = subprocess.run(
                ["tail", "-n", "1000", log_file],
                capture_output=True,
                text=True
            )
            log_lines = result.stdout.strip()
            
            # Check for both error patterns
            if "Token refresh failed with status 403" in log_lines:
                print("Found authentication error in logs: Token refresh failed with status 403")
                return "expired"
            elif "Authentication failed with status 403" in log_lines:
                print("Found authentication error in logs: Authentication failed with status 403")
                return "expired"
            elif "Authentication token refreshed successfully" in log_lines:
                print("Found successful token refresh in logs")
                return "valid"
        except Exception as e:
            print(f"Error checking authentication status in {log_file}: {e}")
    
    # If we've checked all log files and found nothing, return None
    print("No authentication status information found in any log file")
    return None

def is_monitor_running():
    """Check if the monitor process is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "monitor_pnl_hardened.py"],
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except Exception:
        return False

def cleanup_resources(pid_file=None):
    """Clean up resources before exiting"""
    if pid_file and os.path.exists(pid_file):
        try:
            os.remove(pid_file)
            print(f"Removed PID file {pid_file}")
        except Exception as e:
            print(f"Failed to remove PID file: {e}")
    
    send_notification("Webull Watchdog Stopped", "Watchdog process has been terminated", True)

def setup_signal_handlers(pid_file):
    """Set up signal handlers for graceful termination"""
    def signal_handler(sig, frame):
        print(f"Received signal {sig}, shutting down gracefully")
        cleanup_resources(pid_file)
        sys.exit(0)
    
    # Register common termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    
    # Register cleanup to run on normal exit
    atexit.register(lambda: cleanup_resources(pid_file))
    
    print("Signal handlers registered for graceful shutdown")

def main():
    # Directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # PID file to prevent multiple watchdog instances
    pid_file = os.path.join(parent_dir, ".watchdog.pid")
    
    # Check if another instance is already running
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process with this PID exists and is a watchdog
            try:
                # Check if process exists
                os.kill(old_pid, 0)
                
                # Check if it's actually our watchdog
                proc_name = subprocess.run(
                    ["ps", "-p", str(old_pid), "-o", "command="],
                    capture_output=True, 
                    text=True
                ).stdout.strip()
                
                if "simple_watchdog.py" in proc_name:
                    print(f"Another watchdog instance is already running with PID {old_pid}")
                    return 0
            except OSError:
                # Process doesn't exist, we can proceed
                print(f"Found stale PID file for PID {old_pid}, will overwrite")
        except Exception as e:
            print(f"Error checking existing watchdog: {e}")
    
    # Write our PID to the file
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        print(f"Wrote PID {os.getpid()} to {pid_file}")
    except Exception as e:
        print(f"Warning: Could not write PID file: {e}")
    
    # Set up signal handlers with the pid_file
    setup_signal_handlers(pid_file)
    
    # Path to monitor script
    monitor_script = os.path.join(parent_dir, "core_monitoring", "monitor_pnl_hardened.py")
    
    # Get command line arguments
    args = sys.argv[1:]
    
    # Load configuration from .env file
    env_config = load_env_config()
    
    # Ensure test mode is enabled
    if not any(arg == "--test" for arg in args):
        args.append("--test")
        
    # Ensure threshold is set (from .env or default)
    if not any(arg.startswith("--threshold") for arg in args):
        threshold = env_config.get('DEFAULT_THRESHOLD', '-650')
        args.append(f"--threshold={threshold}")
    
    # Ensure test-pnl is set (from .env or default) if in test mode
    if "--test" in args and not any(arg.startswith("--test-pnl") for arg in args):
        test_pnl = env_config.get('TEST_PNL', '-250')
        args.append(f"--test-pnl={test_pnl}")
    
    # Build the command
    cmd = ["python3", monitor_script] + args
    print(f"Starting monitor with command: {' '.join(cmd)}")
    
    # Send startup notification
    send_notification("Webull Monitor Starting", "Kill switch monitor is starting up", True)
    
    # Start the monitor script
    try:
        process = subprocess.Popen(cmd)
        print(f"Monitor started with PID: {process.pid}")
        print("Monitor is running with test mode enabled for token refresh")
        
        # Track idle/active state and last check time
        was_running = True
        last_auth_check = time.time()
        last_auth_status = None
        auth_notification_sent = False
        
        # Keep script running to maintain the shell session
        try:
            while True:
                time.sleep(10)
                
                # Check if process is still running
                is_running = is_monitor_running()
                if not is_running and was_running:
                    print("Monitor process has stopped, restarting...")
                    send_notification("Webull Monitor Stopped", "Monitor process has stopped and is restarting", True)
                    process = subprocess.Popen(cmd)
                    print(f"Restarted monitor with PID: {process.pid}")
                    was_running = True
                    
                # Check for idle/active state changes (every 5 minutes)
                current_time = time.time()
                if current_time - last_auth_check >= 300:  # 5 minutes
                    # Check authentication status
                    auth_status = check_authentication_status()
                    
                    # Only notify if status changed or we haven't sent a notification yet
                    if auth_status == "expired" and (last_auth_status != "expired" or not auth_notification_sent):
                        send_notification("Webull Authentication Expired", 
                                         "Your Webull token has expired. Please run update_token.py to update it.", 
                                         True)
                        auth_notification_sent = True
                    
                    # Reset notification flag if token is valid again
                    if auth_status == "valid" and last_auth_status == "expired":
                        send_notification("Webull Authentication Restored", 
                                         "Your Webull token has been refreshed successfully.", 
                                         True)
                        auth_notification_sent = False
                    
                    last_auth_status = auth_status
                    last_auth_check = current_time
                    
        except KeyboardInterrupt:
            print("Exiting watchdog due to keyboard interrupt")
            send_notification("Webull Monitor Stopped", "Monitor has been manually stopped", True)
            # Clean up PID file
            try:
                os.remove(pid_file)
                print(f"Removed PID file {pid_file}")
            except Exception as e:
                print(f"Failed to remove PID file: {e}")
            
    except Exception as e:
        print(f"Error starting monitor: {e}")
        send_notification("Webull Monitor Error", f"Error starting monitor: {e}", True)
        # Clean up PID file
        try:
            os.remove(pid_file)
        except:
            pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 