import time
import base64
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def canonicalize(headers_to_sign):
    """
    Sorts the header keys and concatenates the trimmed header values with newline characters.
    Returns a tuple: (concatenated parameter names, canonicalized string of values).
    """
    sorted_keys = sorted(headers_to_sign.keys())
    # Build a string of sorted header names separated by semicolons (optional)
    parameter_names = ';'.join(key.strip() for key in sorted_keys) + ';'
    # Build the canonical string by concatenating each trimmed header value followed by a newline
    canonicalized_str = ''.join(headers_to_sign[key].strip() + '\n' for key in sorted_keys)
    return parameter_names, canonicalized_str

def generate_signature(private_key, string_to_sign):
    """
    Signs the string_to_sign using the RSA private key with SHA256 and returns a Base64-encoded signature.
    """
    signature = private_key.sign(
        string_to_sign.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

# Load the RSA private key from PEM file
with open("../../walmart_private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None  # Add a password if your key is encrypted
    )

# Set your header values
consumer_id = "2b327958-c834-40e2-bd3f-731807c07e80"  # Your generated consumer ID
key_version = "3"  # Private key version
timestamp = str(int(time.time() * 1000))  # Current Unix epoch time in milliseconds

# Create the dictionary of headers to sign
headers_to_sign = {
    "WM_CONSUMER.ID": consumer_id,
    "WM_CONSUMER.INTIMESTAMP": timestamp,
    "WM_SEC.KEY_VERSION": key_version
}

# Canonicalize the header values (the Java sample signs the canonicalized values)
_, canonicalized_str = canonicalize(headers_to_sign)

# Generate the signature
signature = generate_signature(private_key, canonicalized_str)

# Build the full set of headers required by the Walmart API
api_headers = {
    "WM_CONSUMER.ID": consumer_id,
    "WM_CONSUMER.INTIMESTAMP": timestamp,
    "WM_SEC.KEY_VERSION": key_version,
    "WM_SEC.AUTH_SIGNATURE": signature,
}

# (Optional) Print the generated headers for debugging
print("Generated API Headers:")
for key, value in api_headers.items():
    print(f"{key}: {value}")

# Example of sending a GET request to the Walmart API (update URL and parameters as needed)
url = "https://developer.api.walmart.com/api-proxy/affil/product/v2/search"
params = {"query": "laptop"}  # Modify according to your API endpoint requirements

response = requests.get(url, headers=api_headers, params=params)
print("Status Code:", response.status_code)
print("Response Body:", response.text)
