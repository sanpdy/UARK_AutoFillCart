Authored by: Stephen Pierson

Updated: 04/14/2025

# Walmart Affiliate API Quickstart Guide with Python

The following steps will get you up and running quickly with the Walmart Affiliate Marketing API and provide setup code to send requests from Python. At the time of writing, the quickstart guide on walmart.io is incomplete, encourages you to write unsecure code, and expects you to make your first request with Java (gross), so this guide addresses those issues.

## Step 1: Create Your Account

Before you can begin, you will need to go to https://www.walmart.io/docs/affiliates/v1/introduction on the web and log in with your Walmart.com account. If you don't have one, you can create one there.

## Step 2: Create Your Application

Navigate to the Dashboard by clicking on your profile icon in the top right. On the left-hand panel, there should be an 'Applications' tab. Click the button to create a new application. You will be asked to enter details about your application so you can link it to your account for future reference.

## Step 3: Generate and Upload Your RSA Key Pair

### Generate Your Key Files

In order for Walmart to authenticate your API requests, you need to upload an RSA public key to for your application in the walmart.io portal.

If you do not have an RSA key pair (or have lost it), you can make one. After navigating to the directory you want to create your RSA key files in with the terminal, you can follow these [steps](https://www.walmart.io/key-tutorial) (compatible with Unix/Mac & Windows) to create a compatible RSA public/private key set. Give your keys a name.

**NOTE**: It is recommended to create your first RSA key set **without** a password as it complicates the process of making Python requests.

If you are unsure of which created file is the public key and which is the private key, the public key should look something like this if you open it in a text editor:

```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCm+LSCbBniaqUd6aYE/zPT0ttgQjkyjykLU3oXgUrDhYGlpRo8cb/4UkAMY1+Nn+UQiM2EV1MYAJuerjxqMOmCDN2tAAafqymgFdjz2vr0yQqL01AsNEXZN7yW0ExvDOvvs6NJk2LW6uhhmt031j7YdAMdIwGLqQ98Olk8xnwaUDGUASUAfBVnHYJoY1sPAs0eNszHJj4CkYK0f4wYOOc5w9O04haFuSfBfReOwTNd7DAzYjKrfttg16pozml3kK5mhcdNm1adpuOVJ9QVuA6BkDCcNpSgkGY+Iwxf0sdZNXGmtnXQjWqzURabHh/NkZIcqCUsebvD1JOdnkWjlojLORs6fxuq/zw7vKIVyuyDbfoROldU8959c1o6jj2XpMofXrEOOxj3msp5jF7emMQDSFlpUQQq6tZgDY/pEdktHjuNs/QjtTdSrRFF5MkTV3Jr90GsrKqFrHjaw08mD2FWPI8olxLJm3hqry4mh93N6+j3Yzqo4V5ZM+KinUXiM10= user@DESKTOP-xxxxxxx
```

**IMPORTANT**: It is critical that you keep your RSA private key private. If it gets shared with someone else, they can use it to abuse your access to the API.

The steps on walmart.io (at the time of writing) DO NOT tell you how to convert your private RSA key to the "pem" file format the code provided further down in this guide requires to send API requests. If you followed the linked steps, your file is likely in OpenSSL format. Your file is only in "pem" format if it has "-----BEGIN PRIVATE KEY-----" and "-----END PRIVATE KEY-----" headers. For that, you'll need to execute a separate command. Use the following command to convert your key to PEM format:

For Windows:
```terminal
ssh-keygen -p -f path\to\your\private_key -m PKCS8
```

For Unix/Mac:
Untested, but probably the same as Windows. Ask ChatGPT.

### Upload Your Key to the Walmart Portal

Follow the steps linked above to copy and paste the public key to the key upload page by executing command. The text should be bounded by "-----BEGIN PUBLIC KEY-----" and "-----END PUBLIC KEY-----", but do not include these headers in the Walmart portal.

After you have uploaded the public key to the walmart.io portal, a **consumer id** will be generated for your application. Make a note of this for making requests to the API next.

## Step 4: Run a Query

Below is some starter code to get you up and running with making some Walmart API requests. It handles creating and injecting the API signature and other request headers into your queries. You may need to install the python cryptography library -> use: `pip install cryptography`. It is not comprehensive, but hopefully you can figure out how to build on the `WalmartAPI` wrapper class using the [API documentation](https://walmart.io/docs/affiliates/v1/catalog-product) provided by Walmart. Happy coding!

```python
import json
import warnings

import requests
import time
import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def filter_walmart_search_result_props(search_results: list[dict]):
    """
    Filter and include only selected properties for available items.

    Parameters:
        search_results (list of dict): The raw search results.
    Returns:
        list of dict: The filtered search results.
    """
    props_to_include = [
        "itemId",
        "name",
        "salePrice",
        "size",
    ]
    filtered_results = []
    for item in search_results:
        if item.get('stock') != "Available":
            continue
        if item.get('offerType') not in ["ONLINE_AND_STORE", "STORE_ONLY"]:
            continue
        filtered_props = {prop: item[prop] for prop in props_to_include if prop in item}
        filtered_results.append(filtered_props)
    return filtered_results


class WalmartAPI:
    def __init__(self, consumer_id: str, key_version: str, key_file_path: str):
        """
        Initialize the WalmartAPI instance with Walmart-specific credentials.
        """
        self.consumer_id = consumer_id
        self.key_version = key_version
        self.key_file_path = key_file_path

    def generate_walmart_request_headers(self) -> dict:
        """
        Generate Walmart API headers with a timestamp and signature.

        Reads the private key from the file specified in the instance,
        constructs a canonicalized string from header values, signs it using
        SHA256 with RSA (PKCS1v15 padding), and returns a dictionary
        containing all the required headers.
        """
        # Get current timestamp in milliseconds
        timestamp = str(int(time.time() * 1000))

        # Load the private key from the instance's file path
        try:
            with open(self.key_file_path, "rb") as key_file:
                key_data = key_file.read()
        except IOError as e:
            raise RuntimeError(f"Error reading the private key file: {e}")

        try:
            private_key = serialization.load_pem_private_key(key_data, password=None)
        except Exception as e:
            raise RuntimeError(f"Error loading private key: {e}")

        # Create base headers using instance attributes
        headers = {
            "WM_CONSUMER.ID": self.consumer_id,
            "WM_CONSUMER.INTIMESTAMP": timestamp,
            "WM_SEC.KEY_VERSION": self.key_version,
        }

        # Build canonicalized string: sorted keys, trimmed values, each ended with a newline.
        canonicalized_str = ""
        for key in sorted(headers.keys()):
            canonicalized_str += headers[key].strip() + "\n"

        # Sign the canonicalized string with RSA using SHA256
        try:
            signature_bytes = private_key.sign(
                canonicalized_str.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        except Exception as e:
            raise RuntimeError(f"Error generating signature: {e}")

        # Base64-encode the signature and add it to the headers
        signature_base64 = base64.b64encode(signature_bytes).decode("ascii")
        headers["WM_SEC.AUTH_SIGNATURE"] = signature_base64

        return headers

    @staticmethod
    def with_walmart_headers(method):
        """
        Decorator that automatically injects Walmart request headers into
        the decorated instance method as a keyword argument 'headers'.
        """

        def wrapper(self, *args, **kwargs):
            headers = self.generate_walmart_request_headers()
            return method(self, *args, headers=headers, **kwargs)

        return wrapper

    @with_walmart_headers
    def get_walmart_taxonomy(self, *, headers: dict) -> str:
        """
        Fetch taxonomy information from the Walmart API.

        The decorator automatically adds the required headers.

        Returns:
            str: Raw response text from the API.
        """
        url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/taxonomy"
        try:
            response = requests.get(url, headers=headers)
            return response.text
        except requests.RequestException as error:
            print("An error occurred during the request:", error)
            return ""

    @with_walmart_headers
    def get_walmart_search_results(self, search_term: str, *, headers: dict) -> str:
        """
        Search for products using the Walmart API.

        The decorator automatically provides the headers.
        Parameters:
            search_term (str): The query string.
        Returns:
            str: Raw response text from the API.
        """
        url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search?query={search_term}"
        try:
            response = requests.get(url, headers=headers)
            return response.text
        except requests.RequestException as error:
            print("An error occurred during the request:", error)
            return ""

    @with_walmart_headers
    def get_stores_nearby(self, zip_code: str, *, headers: dict) -> str:
        """
        Fetch nearby store information using the Walmart API.

        The decorator automatically provides the headers.

        Parameters:
            zip_code (str): The postal code to search near.
        Returns:
            str: Raw response text from the API.
        """
        url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/stores?zip={zip_code}"
        try:
            response = requests.get(url, headers=headers)
            return response.text
        except requests.RequestException as error:
            print("An error occurred during the request:", error)
            return ""

    @with_walmart_headers
    def lookup_walmart_product(self, itemId: int, storeId: int = None, zipCode: str = None, *, headers: dict):
        """
        Lookup Walmart product details using the Walmart API.

        The decorator automatically provides the headers.

        Parameters:
            itemId (int): Product IDs to lookup.
            storeId (int): Store ID for the lookup.
            zipCode (str): Zip code for the lookup.
        Returns:
            str: Raw response text from the API.
        """
        if storeId:
            url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items?ids={itemId}&storeId={storeId}"
        elif zipCode:
            url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items?ids={itemId}&zipCode={zipCode}"
        else:
            url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items?ids={itemId}"
        try:
            print("Requesting URL:", url)
            response = requests.get(url, headers=headers)
            return response.text
        except requests.RequestException as error:
            print("An error occurred during the request:", error)
            return ""


    @staticmethod
    def generate_walmart_cart_url(items: list[dict]) -> str:
        """
        Generate a Walmart shopping cart URL by concatenating item IDs and quantities.

        Parameters:
            items (list of dict): Each dict should have 'item_id' and 'quantity' keys.
        Returns:
            str: URL for adding items to the Walmart cart.
        """
        items_parameter = "items="
        for item in items:
            itemId = item.get('itemId')
            items_parameter += f"{itemId}"
            item_quantity = int(item.get('quantity'))
            if item_quantity < 1:
                # Skip the item if its quantity is less than one
                warnings.warn(f"Skipping item {itemId} with {item_quantity} quantity", RuntimeWarning)
                continue
            elif item_quantity != 1:
                # Include quantity in the URL if it exists and is not "1"
                items_parameter += f"_{item_quantity}"
            items_parameter += ","
        items_parameter = items_parameter.rstrip(',')
        return f"https://affil.walmart.com/cart/addToCart?{items_parameter}"


# Example usages:
if __name__ == "__main__":
    # Create an instance of WalmartAPI with your credentials.
    walmart_api = WalmartAPI(
        consumer_id="your_consumer_id_from_walmart",
        key_version="your_key_version_from_walmart",
        key_file_path=r"path\to\your\rsa_private_key"
    )

    # # Example: Get Walmart website taxonomy
    # taxonomy_str = walmart_api.get_walmart_taxonomy()
    # try:
    #     taxonomy_json = json.loads(taxonomy_str)
    #     print("Taxonomy:", json.dumps(taxonomy_json, indent=2))
    # except json.JSONDecodeError:
    #     print("Taxonomy response (raw):", taxonomy_str)

    # # Example: Get Walmart product search results and filter properties.
    # search_term = "corned beef"
    # search_results_str = walmart_api.get_walmart_search_results(search_term)
    # try:
    #     search_results_json = json.loads(search_results_str)
    #     filtered_results = filter_walmart_search_result_props(search_results_json.get('items', []))
    #     print("Filtered Search Results:", json.dumps(search_results_json, indent=2))
    # except json.JSONDecodeError:
    #     print("Search results response (raw):", search_results_str)

    # # Example: Get nearby stores
    # zip_code = "72701"
    # nearby_stores_str = walmart_client.get_stores_nearby(zip_code)
    # try:
    #     nearby_stores_json = json.loads(nearby_stores_str)
    #     print("Nearby Stores:", json.dumps(nearby_stores_json, indent=2))
    # except json.JSONDecodeError:
    #     print("Nearby stores response (raw):", nearby_stores_str)

    # # Example: Lookup Walmart product details
    # product_ids = [10451002, 27935840, 10309105]
    # product_lookup_str = walmart_api.lookup_walmart_product(10451002)
    # try:
    #     product_lookup_json = json.loads(product_lookup_str)
    #     print("Product Lookup Results:", json.dumps(product_lookup_json, indent=2))
    # except json.JSONDecodeError:
    #     print("Product lookup response (raw):", product_lookup_str)

    # Example: Generate a Walmart cart URL
    example_items = [
        {"itemId": "10451002", "quantity": "1"},  # vegetable oil
        {"itemId": "756616069", "quantity": "2"},  # chicken breast meat
    ]
    cart_url = WalmartAPI.generate_walmart_cart_url(example_items)
    print("Cart URL:", cart_url)

```