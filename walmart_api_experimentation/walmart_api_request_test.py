import requests

# Replace with the correct API endpoint if necessary.
url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/taxonomy"

# Replace 'YOUR_CONSUMER_ID_KEY' with your actual consumer-id key.
headers = {
    "WM_CONSUMER.ID": "2b327958-c834-40e2-bd3f-731807c07e80",
    "Content-Type": "application/json"  # This header is often required, but check the API docs.
}

# Making a GET request. Change to .post() if the API expects a POST request.
response = requests.get(url, headers=headers)

# Check the response status and print data accordingly.
if response.status_code == 200:
    data = response.json()  # Parse JSON response into a Python dictionary.
    print("Response received:")
    print(data)
else:
    print(f"Request failed with status code {response.status_code}")
    print("Error details:", response.text)
