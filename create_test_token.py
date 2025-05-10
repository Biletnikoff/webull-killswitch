#!/usr/bin/env python3
"""
Create Test Token
Utility script to create a test token file for testing the token refresh mechanism
"""
import os
import json
from datetime import datetime, timedelta
import uuid

def create_test_token():
    """Create a test token file with mock data"""
    # Path to token file
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webull_token.json")
    
    # Mock data
    token_data = {
        'access_token': f"test_access_token_{uuid.uuid4().hex[:8]}",
        'refresh_token': f"test_refresh_token_{uuid.uuid4().hex[:8]}",
        'token_expiry': (datetime.now() + timedelta(hours=24)).isoformat(),
        'user_id': '12345678',
        'device_id': f"test_device_id_{uuid.uuid4().hex[:8]}",
        'last_updated': datetime.now().isoformat()
    }
    
    # Save to file
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"Created test token file at {token_file}")
    print(f"Access Token: {token_data['access_token']}")
    print(f"Refresh Token: {token_data['refresh_token']}")
    print(f"Device ID: {token_data['device_id']}")
    print(f"Expiry: {token_data['token_expiry']}")
    
    # Also create a device ID file
    device_id_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "did.bin")
    with open(device_id_file, 'w') as f:
        f.write(token_data['device_id'])
    
    print(f"Created device ID file at {device_id_file}")
    
    return token_data

if __name__ == "__main__":
    create_test_token() 