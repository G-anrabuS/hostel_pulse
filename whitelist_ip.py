import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

# Load env variables
load_dotenv()

ATLAS_GROUP_ID = os.getenv("ATLAS_GROUP_ID")
ATLAS_API_KEY_PUBLIC = os.getenv("ATLAS_API_KEY_PUBLIC")
ATLAS_API_KEY_PRIVATE = os.getenv("ATLAS_API_KEY_PRIVATE")

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except Exception:
        return None

ip = get_public_ip()

if not ip:
    print("❌ Could not fetch public IP")
    exit(1)

url = f"https://cloud.mongodb.com/api/atlas/v1.0/groups/{ATLAS_GROUP_ID}/accessList"

response = requests.post(
    url,
    auth=HTTPDigestAuth(ATLAS_API_KEY_PUBLIC, ATLAS_API_KEY_PRIVATE),
    json=[{
        "ipAddress": ip,
        "comment": "auto-added by script"
    }]
)

if response.status_code in (200, 201):
    print(f"✅ IP {ip} added to MongoDB Atlas access list")
else:
    print("❌ Failed to add IP")
    print(response.status_code, response.text)
