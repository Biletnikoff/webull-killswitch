#!/usr/bin/env python3
"""
Respawn Monitor Script
Responsible for starting and monitoring the Webull Kill Switch monitor process
"""
import os
import sys
import time
import logging
import argparse
import subprocess
import signal
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "respawn.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MONITOR_SCRIPT = os.path.join(SCRIPT_DIR, "monitor_pnl_hardened.py")
WATCHDOG_SCRIPT = os.path.join(SCRIPT_DIR, "watchdog.py")
CHECK_INTERVAL = 30  # seconds
MAX_RESTARTS = 5  # Maximum number of consecutive restarts before giving up
COOL_DOWN_PERIOD = 300  # seconds to wait after hitting max restarts

def create_watchdog_script():
    """Create the watchdog script if it doesn't exist"""
    if os.path.exists(WATCHDOG_SCRIPT):
        logger.info(f"Watchdog script already exists at {WATCHDOG_SCRIPT}")
        return WATCHDOG_SCRIPT
        
    logger.info(f"Creating watchdog script at {WATCHDOG_SCRIPT}")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(SCRIPT_DIR, "logs"), exist_ok=True)
    
    watchdog_content = '''#!/usr/bin/env python3
"""
Watchdog script for Webull Kill Switch
Ensures the monitor script is always running
"""
import os
import sys
import time
import signal
import logging
import subprocess
from datetime import datetime, timedelta

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "watchdog.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MONITOR_SCRIPT = os.path.join(SCRIPT_DIR, "monitor_pnl_hardened.py")
CHECK_INTERVAL = 30  # seconds
RESTART_COOLDOWN = 60  # seconds between restarts
MAX_CONSECUTIVE_RESTARTS = 5
RESTART_RESET_TIME = 3600  # seconds (1 hour) before resetting restart counter

# Keep track of consecutive restarts
restart_count = 0
last_restart_time = None

def find_monitor_process():
    """Find running monitor process"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"python.*{os.path.basename(MONITOR_SCRIPT)}"],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split('\\n')
        return [pid for pid in pids if pid]
    except Exception as e:
        logger.error(f"Error finding monitor process: {e}")
        return []

def is_script_running():
    """Check if the monitor script is running"""
    pids = find_monitor_process()
    return len(pids) > 0

def start_script(args):
    """Start the monitor script with the provided arguments"""
    global restart_count, last_restart_time
    
    try:
        # Use test mode for token refresh
        cmd = ["python3", MONITOR_SCRIPT]
        cmd.extend(args)
        
        logger.info(f"Starting monitor script with: {' '.join(cmd)}")
        subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Update restart tracking
        restart_count += 1
        last_restart_time = datetime.now()
        
        logger.info(f"Monitor script started (restart {restart_count}/{MAX_CONSECUTIVE_RESTARTS})")
        return True
    except Exception as e:
        logger.error(f"Failed to start monitor script: {e}")
        return False

def reset_restart_counter():
    """Reset the restart counter if it's been long enough since the last restart"""
    global restart_count, last_restart_time
    
    if last_restart_time is None:
        return
    
    # If it's been long enough since the last restart, reset the counter
    if (datetime.now() - last_restart_time).total_seconds() > RESTART_RESET_TIME:
        logger.info(f"Resetting restart counter (was {restart_count}, now 0)")
        restart_count = 0

def main():
    """Main watchdog function"""
    logger.info(f"=== Watchdog started (PID: {os.getpid()}) ===")
    
    # Get arguments from respawn_monitor.py
    args = sys.argv[1:]
    logger.info(f"Arguments received: {args}")
    
    # When testing, make sure to use test mode for token refresh
    if "--test" in args:
        logger.info("Test mode detected - will use test mode for authentication")
    
    try:
        while True:
            # Check if monitor script is running
            if not is_script_running():
                logger.warning("Monitor script is not running")
                
                # Check if we've hit max consecutive restarts
                if restart_count >= MAX_CONSECUTIVE_RESTARTS:
                    logger.error(f"Hit maximum consecutive restarts ({MAX_CONSECUTIVE_RESTARTS}), cooling down for {RESTART_COOLDOWN} seconds")
                    time.sleep(RESTART_COOLDOWN)
                    restart_count = 0
                else:
                    # Start the script
                    start_script(args)
                    
                    # Wait a bit to avoid rapid restarts
                    time.sleep(RESTART_COOLDOWN)
            else:
                logger.debug("Monitor script is running")
                # Reset restart counter if it's been long enough
                reset_restart_counter()
            
            # Sleep before next check
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user")
    except Exception as e:
        logger.error(f"Watchdog error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

    # Write the watchdog script
    with open(WATCHDOG_SCRIPT, 'w') as f:
        f.write(watchdog_content)
    
    # Make the script executable
    try:
        os.chmod(WATCHDOG_SCRIPT, 0o755)
        logger.info(f"Made watchdog script executable: {WATCHDOG_SCRIPT}")
    except Exception as e:
        logger.error(f"Failed to make watchdog script executable: {e}")
    
    return WATCHDOG_SCRIPT

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Start and monitor the Webull Kill Switch')
    parser.add_argument('--threshold', type=float, default=-300, help='P/L threshold to trigger the kill switch')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test-pnl', type=float, default=None, help='Test P/L value to use in test mode')
    args = parser.parse_args()
    
    # Set up trap for SIGINT and SIGTERM
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create logs directory
    os.makedirs(os.path.join(SCRIPT_DIR, "logs"), exist_ok=True)
    
    # Ensure watchdog script exists
    watchdog_path = create_watchdog_script()
    logger.info(f"Watchdog script: {watchdog_path}")
    
    # Build arguments for the monitor script
    monitor_args = []
    if args.test:
        monitor_args.append("--test")
    if args.verbose:
        monitor_args.append("--verbose")
    if args.threshold:
        monitor_args.append(f"--threshold={args.threshold}")
    if args.test_pnl is not None:
        monitor_args.append(f"--test-pnl={args.test_pnl}")
    
    # Start the watchdog process
    logger.info("Starting watchdog process")
    try:
        # Pass arguments along to the watchdog script
        watchdog_cmd = ["python3", watchdog_path] + monitor_args
        logger.info(f"Watchdog command: {' '.join(watchdog_cmd)}")
        
        subprocess.Popen(
            watchdog_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        logger.info("Watchdog process started")
        print(f"Webull Kill Switch started with threshold: ${args.threshold:.2f}")
        if args.test:
            print("Running in TEST MODE")
        
        print("Monitor and watchdog processes are running in the background")
        print("Check logs/watchdog.log and logs/monitor_hardened.log for details")
    except Exception as e:
        logger.error(f"Failed to start watchdog: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 