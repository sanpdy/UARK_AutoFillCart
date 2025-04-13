import requests
from bs4 import BeautifulSoup
import json

# Replace this with the actual URL you are scraping
url = "https://www.walmart.com/search?q=xbox"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}
session = requests.Session()
response = session.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
print("Soup:", soup)

# Find all product containers using the classes from the snippet
containers = soup.select("div.mb0.ph0-xl.pt0-xl.bb.b--near-white.w-25.pb3-m.ph1")
results = []

for container in containers:
    # Find the <a> element with the product URL using the 'link-identifier' attribute
    link_element = container.select_one("a[link-identifier]")
    # Find the element containing the product title using the data-automation-id attribute
    title_element = container.select_one('[data-automation-id="product-title"]')

    if link_element and title_element:
        product_url = link_element.get("href")
        title = title_element.get_text(strip=True)
        results.append({"title": title, "url": product_url})

# Output the results as a JSON object
print(json.dumps(results, indent=2))
