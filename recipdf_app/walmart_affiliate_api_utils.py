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
        consumer_id="fe944cf5-2cd6-4664-8d8a-1a6e0882d722",
        key_version="1",
        key_file_path=r"C:\Users\joshuaupshaw\Desktop\rsa_key_20250410_v2"
    )

    # walmart_api = WalmartAPI(
    #     consumer_id="692e16e8-25dc-4df4-a040-e20a77ef9d73",
    #     key_version="3",
    #     key_file_path=r"C:\Users\Stephen Pierson\.ssh\setup_test"
    # )

    # Example: Get Walmart website taxonomy
    taxonomy_str = walmart_api.get_walmart_taxonomy()
    try:
        taxonomy_json = json.loads(taxonomy_str)
        print("Taxonomy:", json.dumps(taxonomy_json, indent=2))
    except json.JSONDecodeError:
        print("Taxonomy response (raw):", taxonomy_str)

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
