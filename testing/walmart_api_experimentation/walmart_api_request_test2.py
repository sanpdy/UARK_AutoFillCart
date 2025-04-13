import time
import base64
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Set your API credentials and file path
consumer_id = "625f6595-fa22-4014-99b6-9c5c6e86b117"  # Your actual consumer ID
key_version = "3"  # Provided in your API credentials (could be "1" or "2")
private_key_file = r"C:\Users\Stephen Pierson\.ssh\rsa_key_file"  # Path to your new RSA private key file

# Load the private key using load_pem_private_key (since it's now in RSA PEM format)
with open(private_key_file, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None  # No passphrase required if the key is unencrypted
    )

# Generate the current timestamp in milliseconds
timestamp = str(int(time.time() * 1000))

# Create the canonical string to sign: WM_CONSUMER.ID, WM_CONSUMER.INTIMESTAMP, WM_SEC.KEY_VERSION (each followed by a newline)
data_to_sign = f"{consumer_id}\n{timestamp}\n{key_version}\n".encode('utf-8')

# Generate the signature using RSA with SHA-256 and PKCS#1 v1.5 padding
signature = private_key.sign(
    data_to_sign,
    padding.PKCS1v15(),
    hashes.SHA256()
)
# Base64 encode the signature to include in the header
signature_b64 = base64.b64encode(signature).decode('utf-8')

# Prepare the headers with all required security information
headers = {
    "WM_CONSUMER.ID": consumer_id,
    "WM_CONSUMER.INTIMESTAMP": timestamp,
    "WM_SEC.KEY_VERSION": key_version,
    "WM_SEC.AUTH_SIGNATURE": signature_b64,
    "Content-Type": "application/json"
}

# API endpoint URL (adjust if necessary)
url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/taxonomy"

# Make the API call (GET request; use post() if required by the API)
response = requests.get(url, headers=headers)

# Process and print the response
if response.status_code == 200:
    data = response.json()
    print("Response received:")
    print(data)
else:
    print(f"Request failed with status code {response.status_code}")
    print("Error details:", response.text)
