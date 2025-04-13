import requests


def main():
    # Walmart API URL for taxonomy
    url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/taxonomy"

    # Define the headers as specified:
    # - WM_SEC.KEY_VERSION: The version of your private key (replace "your_key_version" with the actual version)
    # - WM_CONSUMER.ID: Your assigned consumer id (currently using "placeholder_str")
    # - WM_CONSUMER.INTIMESTAMP: The timestamp in Unix epoch time in milliseconds (provided here as a string)
    # - WM_SEC.AUTH_SIGNATURE: The generated signature using your private key (placeholder "placeholder_str2")
    headers = {
        "WM_SEC.KEY_VERSION": "1",  # Replace with your actual key version
        "WM_CONSUMER.ID": "fe944cf5-2cd6-4664-8d8a-1a6e0882d722",  # Replace with your actual consumer ID
        "WM_CONSUMER.INTIMESTAMP": "1744336515146",  # Unix epoch time in milliseconds
        "WM_SEC.AUTH_SIGNATURE": "cQF8ngV9jMsS+4dSbVxhWZyT2begd+iRy85ENQ2t7TR7mJpAafOEWYr+4yRLWgejTWBi4aAfr9YdV4xWjdCrGDyeGaYQpN/0jabK+s9HsjHGTsdruALYad8HxdWLqOkU5TUUkXH+JwUYh9NFaRlQ4pydcw9QrWC8Bm1ZCWHWLuaeZlol5Zhgs9EDZitdo/ls1Q8TV2+pRVQAcVT331HH0PqHNuNK4/EtXlnGFw3ykfs/ka+oG0/a2kOIdKRMPCv/KTqrfRtpK8jz4xHbuyCwKh3A+wAv++F9mG29p7vygLSH8gJwdZoIC4BxcUxH05+C3RfCSn5HxiL6LypI3Nk0ES5OBWy2r0XhudR8Ij115OBhP7Qq9+IggB5ASLjX9s5t0zlJ1ExQyaMccwT0z22wOjdzku8NlNmBLEL9aEGnVmjRDgWWcAMv7NCyBiyPTJdVQCfFwELdDdpQB0SWJ5SzLUncZKQseg9Ovs0/snaiO38oEjjSskwgyRj19iX9VYMM"  # Replace with your generated signature
    }

    try:
        response = requests.get(url, headers=headers)
        print("Status Code:", response.status_code)
        # Attempt to interpret the response as JSON; if not possible, print the text.
        try:
            data = response.json()
            print("Response JSON:", data)
        except ValueError:
            print("Response Text:", response.text)
    except requests.RequestException as e:
        print("An error occurred during the request:", e)


if __name__ == "__main__":
    main()
