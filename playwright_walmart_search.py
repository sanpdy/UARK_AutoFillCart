from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pydantic import BaseModel


class ItemSchema(BaseModel):
    item_name: str
    product_link: str

    def __str__(self):
        return f"Item Name: {self.item_name}\nProduct Link: {self.product_link}"


def get_walmart_items(search_term: str) -> list[ItemSchema]:
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        # Create a new context with realistic headers
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            }
        )

        page = context.new_page()
        page.goto(f"https://www.walmart.com/search?q={search_term}")
        html = page.inner_html(
            '[data-testid="item-stack"]')  # Use the data-testid to get the inner HTML of the item stack
        # print(html)
        soup = BeautifulSoup(html, "html.parser")
        print(soup)
        print()
        # Find all search result divs by their unique class
        results = soup.find_all("div", class_="mb0 ph0-xl pt0-xl bb b--near-white w-25 pb3-m ph1")

        for result in results:
            # Locate the anchor tag that contains the product link and item name
            a_tag = result.find("a", href=True)
            if a_tag:
                # Extract the product link from the href attribute
                product_link = a_tag['href']
                # Extract the item name from the inner span (using the class as a selector)
                span = a_tag.find("span", class_="w_iUH7")
                item_name = span.get_text(strip=True) if span else "Name not found"
                items.append(ItemSchema(item_name=item_name, product_link=product_link))
    return items


if __name__ == "__main__":
    user_input = input("Enter the search term (e.g., 'carrots'): ").strip().lower()
    search_term = user_input.replace(" ", "+")  # Format the search term for the URL
    search_results = get_walmart_items(search_term)
    for item in search_results:
        print("Item Name:", item.item_name)
        print("Product Link:", item.product_link)
