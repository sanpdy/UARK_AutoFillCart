from wapy.api import Wapy

wapy = Wapy('your-walmart-api-key') # Create an instance of Wapy.

# #### PRODUCT LOOKUP ####
# product = wapy.product_lookup('21853453') # Perform a product lookup using the item ID.
# print(product.name)  # Apple EarPods with Remote and Mic MD827LLA
# print(product.weight)  # 1.0
# print(product.customer_rating)  # 4.445
# print(product.medium_image)  # https://i5.walmartimages.com/asr/6cd9c...

# #### PRODUCT SEARCH ####
# products = wapy.search('xbox')
# for product in products:
#     print(product.name)

#### PRODUCT REVIEWS ####
reviews = wapy.product_reviews('21853453')
for review in reviews:
    print(review.reviewer)
