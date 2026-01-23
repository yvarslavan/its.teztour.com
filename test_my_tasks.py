#!/usr/bin/env python3
"""
Test script to verify MyTasksApp functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_login_and_tasks():
    session = requests.Session()

    # Try to login with a test user (you'll need to provide actual credentials)
    login_data = {
        'username': 'y.varslavan',  # Replace with actual username
        'password': 'your_password'  # Replace with actual password
    }

    print("1. Testing login...")
    try:
        response = session.post(f"{BASE_URL}/users/login", data=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
        elif response.status_code == 302:
            print("✅ Login redirected (likely successful)")
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return

    # Test access to my-tasks page
    print("\n2. Testing access to /tasks/my-tasks...")
    try:
        response = session.get(f"{BASE_URL}/tasks/my-tasks")
        if response.status_code == 200:
            print("✅ My tasks page accessible")
            # Check if MyTasksApp is mentioned in the response
            if "MyTasksApp" in response.text:
                print("✅ MyTasksApp found in page")
            else:
                print("❌ MyTasksApp not found in page")
        else:
            print(f"❌ My tasks page failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ My tasks page error: {e}")

    # Test API endpoint
    print("\n3. Testing API endpoint /tasks/get-my-tasks-paginated...")
    try:
        response = session.get(f"{BASE_URL}/tasks/get-my-tasks-paginated")
        if response.status_code == 200:
            print("✅ API endpoint accessible")
            try:
                data = response.json()
                print(f"✅ API returned JSON with {len(data.get('data', []))} tasks")
            except:
                print("❌ API response is not valid JSON")
        else:
            print(f"❌ API endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ API endpoint error: {e}")

    # Test static files
    print("\n4. Testing static files...")
    static_files = [
        "/static/js/jquery-3.5.1.min.js",
        "/static/js/my_tasks_app.js",
        "/static/js/jquery.dataTables.min.js"
    ]

    for file_path in static_files:
        try:
            response = session.get(f"{BASE_URL}{file_path}")
            if response.status_code == 200:
                print(f"✅ {file_path} - OK")
            else:
                print(f"❌ {file_path} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} - Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing MyTasksApp functionality")
    print("=" * 50)
    print("⚠️  Note: You need to provide valid credentials in the script")
    print("=" * 50)
    test_login_and_tasks()
