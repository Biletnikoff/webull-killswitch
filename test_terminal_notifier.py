#!/usr/bin/env python3
"""
Simple script to test terminal-notifier notifications.
"""
import subprocess
import time
import os
import sys

def test_terminal_notifier():
    """Test terminal-notifier with different parameters for best visibility"""
    
    print("Testing terminal-notifier notifications...")
    
    # Check if terminal-notifier is installed
    try:
        which_result = subprocess.run(
            ["which", "terminal-notifier"], 
            check=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        terminal_notifier_path = which_result.stdout.decode('utf-8').strip()
        print(f"terminal-notifier found at: {terminal_notifier_path}")
    except subprocess.SubprocessError:
        print("ERROR: terminal-notifier not found. Install it with 'brew install terminal-notifier'")
        return False
    
    # Test 1: Basic notification with sound
    print("\nTest 1: Basic notification with sound")
    cmd = [
        "terminal-notifier",
        "-title", "Test Notification 1",
        "-message", "This is a basic test notification with sound",
        "-sound", "Glass"
    ]
    subprocess.run(cmd, check=True)
    time.sleep(3)
    
    # Test 2: Notification with subtitle
    print("\nTest 2: Notification with subtitle")
    cmd = [
        "terminal-notifier",
        "-title", "Test Notification 2",
        "-subtitle", "With Subtitle",
        "-message", "This notification includes a subtitle",
        "-sound", "Glass"
    ]
    subprocess.run(cmd, check=True)
    time.sleep(3)
    
    # Test 3: Notification with alert icon
    print("\nTest 3: Notification with alert icon")
    cmd = [
        "terminal-notifier",
        "-title", "ALERT: Test Notification 3",
        "-subtitle", "Webull Monitor Alert",
        "-message", "This notification includes an alert icon",
        "-contentImage", "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertStopIcon.icns",
        "-sound", "Glass"
    ]
    subprocess.run(cmd, check=True)
    time.sleep(3)
    
    # Test 4: Notification with different sound
    print("\nTest 4: Notification with different sound")
    cmd = [
        "terminal-notifier",
        "-title", "Test Notification 4",
        "-subtitle", "Different Sound",
        "-message", "This notification uses a different sound",
        "-sound", "Submarine"
    ]
    subprocess.run(cmd, check=True)
    time.sleep(3)
    
    # Test 5: Notification that stays on screen
    print("\nTest 5: Notification with activate parameter to keep visible")
    cmd = [
        "terminal-notifier",
        "-title", "IMPORTANT: Test Notification 5",
        "-subtitle", "Webull Kill Switch Alert",
        "-message", "This notification should remain visible",
        "-contentImage", "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/AlertStopIcon.icns",
        "-sound", "Glass",
        "-execute", "open -a Terminal"
    ]
    subprocess.run(cmd, check=True)
    
    print("\nAll test notifications sent. Did you see and hear them?")
    return True

if __name__ == "__main__":
    test_terminal_notifier() 