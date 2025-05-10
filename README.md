# Webull Kill Switch

This automated system monitors your Webull account's profit/loss (P/L) and automatically closes Webull when losses exceed a predefined threshold.

## Features

- Real-time P/L monitoring during market hours
- Configurable loss threshold
- Auto-refreshing authentication
- Resilient watchdog to ensure continuous monitoring
- Notifications for system status
- Test mode for simulating P/L values
- Automatic detection of market hours

## Components

- `monitor_pnl_hardened.py`: Main monitoring script that checks P/L and triggers the kill switch
- `production_watchdog.py`: Ensures the monitor stays running in production
- `simple_watchdog.py`: Simplified watchdog for testing
- `killTradingApp.scpt`: AppleScript that closes the Webull application/tabs
- `check_status.py`: Status checker for the monitoring system
- `cleanup.sh`: Utility to terminate all processes and clean up

## System Architecture & Fault Tolerance

The Webull Kill Switch is designed with reliability and fault tolerance as core principles, using a two-process architecture to ensure continuous monitoring.

### Monitor-Watchdog Relationship

The system operates as a pair of processes with distinct responsibilities:

1. **Monitor Process** (`monitor_pnl_hardened.py`):

   - Primary responsibility: Monitors P/L and triggers the kill switch when threshold is reached
   - Executes the actual trading app termination
   - Includes self-protection mechanisms to prevent accidental termination
   - Handles authentication token refresh and API communication

2. **Watchdog Process** (`production_watchdog.py` or `simple_watchdog.py`):
   - Primary responsibility: Ensures the monitor process is always running
   - Regularly checks if the monitor is active and restarts it if necessary
   - Acts as a "supervisor" for the entire system
   - Provides a stable shell environment for the monitor

### Fault Tolerance Mechanisms

The system includes multiple layers of protection to ensure operation even under adverse conditions:

#### 1. Unkillable Monitor Design

The monitor process is designed to be resistant to accidental termination:

- Uses signal handling to ignore standard termination signals (SIGTERM)
- Requires forced termination (SIGKILL) to be stopped
- Logs all unexpected termination attempts

#### 2. Automatic Regeneration

If the monitor process is forcibly terminated:

- The watchdog detects the termination within seconds
- Automatically respawns the monitor with identical parameters
- Maintains the monitoring threshold and other settings
- Logs the regeneration event for auditing

#### 3. System Hardening

Additional hardening features provide resilience:

- Continues operation during temporary API failures
- Caches authentication tokens to handle authentication server outages
- Tolerates network interruptions with exponential backoff retry logic
- Uses the filesystem to maintain state across restarts

#### 4. Clean Recovery

The `cleanup.sh` script provides a "nuclear option" to reset the system if needed:

- Forcefully terminates all monitor and watchdog processes
- Removes any lock files or stale state
- Allows for a clean restart when necessary

### Practical Implications

This architecture ensures that:

- The kill switch will continue to function even if someone attempts to stop it
- System restarts or crashes are automatically recovered from
- The threshold protection remains in place without human intervention
- Any potential single points of failure are mitigated

In practice, the only way to properly stop the system is through the `cleanup.sh` script, which includes multiple safeguards (confirmation prompts, countdown timers, and verification codes) to prevent impulsive deactivation of your protection. This ensures all components are properly terminated while preventing accidental shutdown of your protection system.

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your settings:
   ```
   DEFAULT_THRESHOLD=-300
   CHECK_INTERVAL=60
   TEST_PNL=-250
   ```
4. Set up authentication by running:
   ```bash
   python3 generate_token.py
   ```
5. Start the system:
   ```bash
   python3 production_watchdog.py
   ```

## Production Usage

For production use, the system can be started with:

```bash
./cleanup.sh && python3 production_watchdog.py
```

This will:

1. Clean up any existing processes
2. Start the monitor in production mode
3. Run only during market hours (6:30am-1:15pm PST on weekdays)
4. Use the watchdog to ensure the monitor stays running

## Testing

For testing, you can use:

```bash
./cleanup.sh && python3 simple_watchdog.py --test --verbose
```

This will:

1. Clean up any existing processes
2. Start the monitor in test mode
3. Use simulated P/L values
4. Run regardless of market hours

## System Status

Check the status of all components with:

```bash
python3 check_status.py
```

## Security Note

This repository uses `.gitignore` to prevent sensitive credentials from being committed. Never commit your Webull tokens or credentials to version control.

## Recent Updates

### Latest Improvements (May 2025)

1. **Enhanced Watchdog System**: Improved the reliability of the watchdog system to ensure the monitor is always running, with better error handling and logging.

2. **Robust Notification System**: Updated the notification system to play sound alerts reliably on macOS using the system sound library.

3. **Better Logging**: Implemented comprehensive logging for both the monitor and watchdog processes, making troubleshooting easier.

4. **System Status Checker**: Added a new `check_status.py` script to verify the status of all components and provide actionable recommendations.

5. **Streamlined Installation**: Completely redesigned the installation and uninstallation scripts with better user feedback and error handling.

6. **Clean Termination**: Added a `cleanup.sh` script to forcibly terminate all processes if they become stuck due to the hardened protection mechanisms.

7. **Simplified Testing**: Created simpler test scripts for easier verification of the system's functionality without full deployment.

8. **Market Hours Logic**: Refined the market hours logic to properly handle weekends and after-hours for better resource usage.
