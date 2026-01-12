import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://127.0.0.1:10443/issues.json?limit=1"
print(f"Testing connection to {url}...")

try:
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    session.proxies.clear()
    session.proxies.update({'http': '', 'https': ''})
    
    response = session.get(url)
    print(f"Status Code: {response.status_code}")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")

