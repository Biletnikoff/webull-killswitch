#!/usr/bin/env python3
import subprocess
import os
import time

# Create a separate AppleScript file for notifications
script_content = '''
display notification "This is a test notification with sound" with title "Sound Test" sound name "Glass"
'''

# Write the script to a file
with open('test_notification.scpt', 'w') as f:
    f.write(script_content)

print("Sending notification with sound...")
# Run the script
subprocess.run(['osascript', 'test_notification.scpt'])

# Wait a bit
time.sleep(2)

# Try a different sound
script_content = '''
display notification "This is a test notification with Submarine sound" with title "Sound Test 2" sound name "Submarine" 
'''
with open('test_notification.scpt', 'w') as f:
    f.write(script_content)

print("Sending notification with Submarine sound...")
subprocess.run(['osascript', 'test_notification.scpt'])

# Wait a bit
time.sleep(2)

# Try playing a direct system sound
print("Playing system sound directly...")
subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])

print("Done. Did you see and hear the notifications?") 