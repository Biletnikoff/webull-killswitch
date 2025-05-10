#!/usr/bin/env python3
"""
Create a simple AppleScript application for more reliable notifications.
This creates a small application that can be used to show notifications with better visibility.
"""
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_notifier_app():
    """Create a simple AppleScript application for notifications"""
    
    # Path for the notifier app
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WebullNotifier.app")
    
    # AppleScript content
    applescript = '''
    on run argv
        set theTitle to item 1 of argv
        set theMessage to item 2 of argv
        
        try
            display notification theMessage with title theTitle subtitle "Webull Monitor" sound name "Glass"
            return "Notification displayed successfully"
        on error errMsg
            return "Error: " & errMsg
        end try
    end run
    '''
    
    # Create a temporary AppleScript file
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_notifier.applescript")
    
    try:
        # Write the AppleScript to a file
        with open(script_path, 'w') as f:
            f.write(applescript)
        
        # Compile the AppleScript into an application
        result = subprocess.run(
            ['osacompile', '-o', app_path, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Make the application executable
        subprocess.run(['chmod', '+x', app_path], check=True)
        
        # Remove the temporary script file
        os.remove(script_path)
        
        logger.info(f"Notification app created at: {app_path}")
        logger.info("To test: run './WebullNotifier.app/Contents/MacOS/applet \"Title\" \"Message\"'")
        return True
    
    except Exception as e:
        logger.error(f"Failed to create notification app: {e}")
        if os.path.exists(script_path):
            os.remove(script_path)
        return False

if __name__ == "__main__":
    create_notifier_app() 