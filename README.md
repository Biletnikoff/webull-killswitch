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
