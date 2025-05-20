#!/usr/bin/env python3
import os
import sys
import platform

# Open a file for writing
with open('debug_output.txt', 'w') as f:
    f.write("Python Debug Information\n")
    f.write("======================\n\n")
    
    # Python version
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Platform: {platform.platform()}\n")
    f.write(f"Working directory: {os.getcwd()}\n\n")
    
    # Environment variables
    f.write("Environment Variables:\n")
    for key, value in sorted(os.environ.items()):
        if 'PATH' in key or 'PYTHON' in key:
            f.write(f"{key}={value}\n")
    
    # List files in current directory
    f.write("\nFiles in current directory:\n")
    for item in sorted(os.listdir('.')):
        if os.path.isfile(item):
            size = os.path.getsize(item)
            f.write(f"{item} - {size} bytes\n")
        else:
            f.write(f"{item}/ (directory)\n")

# Print success message
print("Debug information saved to debug_output.txt") 