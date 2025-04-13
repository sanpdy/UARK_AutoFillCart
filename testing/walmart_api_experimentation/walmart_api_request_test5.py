import time
import base64
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def generate_signature(private_key, string_to_sign):
    """
    Generates a Base64-encoded RSA signature for the provided string using the SHA-256 hash.
    """
    signature = private_key.sign(
        string_to_sign.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

# Load your RSA private key (ensure the path and any password are correct)
with open("../../walmart_private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(key_file.read(), password=None)

# Set your header values (replace with your actual consumer ID and key version)
consumer_id = "692e16e8-25dc-4df4-a040-e20a77ef9d73"     # This is provided once you upload your public key
key_version = "1"                    # Use the key version as assigned by Walmart
timestamp = str(int(time.time() * 1000))  # Current time in milliseconds

# Prepare the headers to sign (order matters: sort keys alphabetically)
headers_to_sign = {
    "WM_CONSUMER.ID": consumer_id,
    "WM_CONSUMER.INTIMESTAMP": timestamp,
    "WM_SEC.KEY_VERSION": key_version
}

# Create the canonicalized string (concatenating the trimmed header values with newline characters)
canonicalized_str = ''.join(headers_to_sign[k].strip() + '\n' for k in sorted(headers_to_sign.keys()))

# Generate the signature from the canonicalized string
signature = generate_signature(private_key, canonicalized_str)

# Build the complete set of API headers required by Walmart
api_headers = {
    "WM_CONSUMER.ID": consumer_id,
    "WM_CONSUMER.INTIMESTAMP": timestamp,
    "WM_SEC.KEY_VERSION": key_version,
    "WM_SEC.AUTH_SIGNATURE": signature,
}

# Define the Taxonomy API endpoint
url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/taxonomy"

# Send the GET request to the endpoint
response = requests.get(url, headers=api_headers)

# Output the status code and the response body (JSON)
print("Status Code:", response.status_code)
print("Response Body:", response.text)
