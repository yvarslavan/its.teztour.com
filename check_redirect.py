import requests
import urllib3
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://127.0.0.1:10443/issues.json?limit=1"

print(f"Testing connection to {url}...")

try:
    # Не следуем за редиректами, чтобы увидеть заголовок Location
    response = requests.get(url, verify=False, allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    if response.status_code in [301, 302, 303, 307, 308]:
        print(f"Redirect Location: {response.headers.get('Location')}")
    else:
        print("No redirect or different status.")
        print(f"Response text preview: {response.text[:200]}")

except Exception as e:
    print(f"Error: {e}")

