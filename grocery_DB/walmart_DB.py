
# Below is an Python script that generates the same grocery data (products, recipes, and recipe ingredients) 
# and outputs them as CSV files. It creates three CSV files:
# 1. products.csv
# 2. recipes.csv
# 3. recipe_ingredients.csv
# You can then load these files into your application (or a database) as needed.
# ⸻
# import os
# os.chdir("git/UARK_AutoFillCart/grocery_DB")
# Make sure to change the path above to the directory where you want to save the CSV files.
# ⸻
# -----------------------------------------------------------------------------
# 1. IMPORTS
# -----------------------------------------------------------------------------
# This script uses the built-in csv module to write CSV files.
# It also uses the random module to generate random product data.
import csv
import random

# -----------------------------------------------------------------------------
# 1. DATA SOURCES (same as your original script)
# -----------------------------------------------------------------------------

CATEGORIES = {
    "Produce": [
        "Apples", "Bananas", "Carrots", "Spinach", "Broccoli", "Lettuce", "Onions",
        "Tomatoes", "Bell Peppers", "Cucumbers", "Grapes", "Strawberries", "Potatoes"
    ],
    "Dairy": [
        "Milk", "Eggs", "Cheese", "Yogurt", "Butter", "Cottage Cheese", "Cream Cheese"
    ],
    "Meats": [
        "Chicken Breast", "Ground Beef", "Pork Chops", "Bacon", "Steak", "Salmon",
        "Shrimp", "Turkey", "Ham"
    ],
    "Pantry": [
        "Rice", "Pasta", "Flour", "Sugar", "Olive Oil", "Baking Powder", "Peanut Butter",
        "Jelly", "Cereal", "Oats", "Beans", "Canned Tuna"
    ],
    "Beverages": [
        "Bottled Water", "Orange Juice", "Apple Juice", "Soda", "Sparkling Water",
        "Coffee", "Tea Bags"
    ],
    "Frozen": [
        "Frozen Pizza", "Frozen Vegetables", "Ice Cream", "Frozen Berries",
        "Frozen French Fries"
    ],
    "Snacks": [
        "Chips", "Cookies", "Crackers", "Popcorn", "Granola Bars", "Mixed Nuts"
    ],
    "Bakery": [
        "Bread", "Bagels", "Muffins", "Donuts", "Tortillas", "Croissants"
    ],
    "Condiments & Sauces": [
        "Salt", "Pepper", "Ketchup", "Mustard", "Mayonnaise", "Soy Sauce", "Vinegar",
        "BBQ Sauce"
    ]
}

BRANDS = [
    "Great Value", "Member's Mark", "Organic Farms", "Kirkland",
    "Heinz", "Del Monte", "Market Pantry", "Private Selection"
]

FULFILLMENT_SPEED_OPTIONS = ["Same Day", "Next Day", "Two Day", "Standard"]
AVAILABILITY_OPTIONS = ["In Stock", "Out of Stock", "Limited Stock"]
WALMART_CASH_OFFERS_OPTIONS = ["Yes", "No"]
GIFTING_OPTIONS = ["No", "Gift Wrap Available"]
BENEFIT_PROGRAMS_OPTIONS = ["N/A", "SNAP Eligible", "WIC Eligible", "Senior Discount"]

DEFAULT_DEPARTMENTS = "Grocery"
DEFAULT_FORM = "N/A"
DEFAULT_FOOD_CONDITION = "Fresh"
DEFAULT_FLAVOR = "N/A"
DEFAULT_MEAT_TYPE = "N/A"
DEFAULT_NUTRITIONAL_CONTENT = "N/A"
DEFAULT_SPECIAL_DIET_NEEDS = "None"
DEFAULT_PREPARATION_METHOD = "N/A"
DEFAULT_CONTAINER = "N/A"
DEFAULT_PACKAGED_MEAL_TYPE = "N/A"
DEFAULT_SIZE_DESCRIPTOR = "N/A"
DEFAULT_RETAILER = "Walmart"

# -----------------------------------------------------------------------------
# 2. RECIPE DATA (unchanged from your script)
# -----------------------------------------------------------------------------

RECIPES = [
    {
        "name": "Spaghetti Marinara",
        "instructions": (
            "Cook pasta according to package directions. Warm marinara sauce in a pan. "
            "Combine pasta with sauce, then season with salt and pepper."
        ),
        "ingredients": [
            ("Pasta", 8, "oz"),
            ("Olive Oil", 2, "tbsp"),
            ("Salt", 1, "tsp"),
            ("Pepper", 0.5, "tsp"),
            ("Tomatoes", 2, "whole (optional garnish)"),
            ("Cheese", 0.25, "cup (optional)")
        ]
    },
    {
        "name": "Chicken Stir-Fry",
        "instructions": (
            "Heat oil in a wok or pan. Stir-fry chicken pieces until cooked. "
            "Add vegetables, soy sauce, and spices. Serve with rice."
        ),
        "ingredients": [
            ("Chicken Breast", 1, "lb"),
            ("Bell Peppers", 2, "whole"),
            ("Onions", 1, "whole"),
            ("Soy Sauce", 2, "tbsp"),
            ("Rice", 1, "cup (uncooked)"),
            ("Olive Oil", 1, "tbsp")
        ]
    },
    {
        "name": "Grilled Cheese Sandwich",
        "instructions": (
            "Butter two slices of bread. Place cheese slices between them. "
            "Grill in a pan until golden brown on both sides."
        ),
        "ingredients": [
            ("Bread", 2, "slices"),
            ("Butter", 1, "tbsp"),
            ("Cheese", 2, "slices")
        ]
    },
    {
        "name": "Garden Salad",
        "instructions": (
            "Chop lettuce, tomatoes, cucumbers, and onions. Toss in a bowl "
            "with dressing. Top with croutons or cheese if desired."
        ),
        "ingredients": [
            ("Lettuce", 1, "head"),
            ("Tomatoes", 2, "whole"),
            ("Cucumbers", 1, "whole"),
            ("Onions", 0.5, "whole"),
            ("Salt", 0.25, "tsp"),
            ("Pepper", 0.25, "tsp")
        ]
    },
    {
        "name": "Pancakes",
        "instructions": (
            "Mix flour, sugar, baking powder, milk, and eggs into a batter. "
            "Cook on a greased griddle until golden on both sides."
        ),
        "ingredients": [
            ("Flour", 1, "cup"),
            ("Sugar", 2, "tbsp"),
            ("Baking Powder", 2, "tsp"),
            ("Milk", 1, "cup"),
            ("Eggs", 1, "whole"),
            ("Butter", 1, "tbsp (for greasing)")
        ]
    }
]

# Number of random products you want to generate
NUM_ITEMS_TO_INSERT = 300

# -----------------------------------------------------------------------------
# 3. GENERATE RANDOM PRODUCT DATA
# -----------------------------------------------------------------------------

def generate_random_product(product_id):
    """
    Return a list/tuple of field values matching the columns we want in CSV.
    We include the product_id so each row has a unique, incrementing ID.
    """
    category = random.choice(list(CATEGORIES.keys()))
    item_name = random.choice(CATEGORIES[category])

    price = round(random.uniform(1.00, 20.00), 2)
    brand = random.choice(BRANDS)
    fulfillment_speed = random.choice(FULFILLMENT_SPEED_OPTIONS)
    availability = random.choice(AVAILABILITY_OPTIONS)
    walmart_cash_offers = random.choice(WALMART_CASH_OFFERS_OPTIONS)
    customer_rating = round(random.uniform(1.0, 5.0), 1)
    gifting = random.choice(GIFTING_OPTIONS)
    benefit_programs = random.choice(BENEFIT_PROGRAMS_OPTIONS)

    return [
        product_id,
        item_name,
        DEFAULT_DEPARTMENTS,
        price,
        brand,
        fulfillment_speed,
        availability,
        walmart_cash_offers,
        customer_rating,
        DEFAULT_FORM,
        DEFAULT_FOOD_CONDITION,
        DEFAULT_FLAVOR,
        DEFAULT_MEAT_TYPE,
        DEFAULT_NUTRITIONAL_CONTENT,
        DEFAULT_SPECIAL_DIET_NEEDS,
        DEFAULT_PREPARATION_METHOD,
        DEFAULT_CONTAINER,
        DEFAULT_PACKAGED_MEAL_TYPE,
        category,
        DEFAULT_SIZE_DESCRIPTOR,
        DEFAULT_RETAILER,
        gifting,
        benefit_programs
    ]

# -----------------------------------------------------------------------------
# 4. MAIN SCRIPT: GENERATE AND WRITE CSVs
# -----------------------------------------------------------------------------

def main():
    # 4.1 Generate products
    products_data = []
    for i in range(1, NUM_ITEMS_TO_INSERT + 1):
        products_data.append(generate_random_product(i))

    # 4.2 Generate recipes and recipe_ingredients
    #     We'll store them as simple lists of lists, so we can write them to CSV
    recipes_data = []
    recipe_ingredients_data = []

    # We'll auto-increment recipe_id ourselves
    recipe_id_counter = 1
    ingredient_id_counter = 1  # If you wanted separate IDs for each ingredient row

    for recipe in RECIPES:
        # Add recipe row
        recipe_row = [
            recipe_id_counter,
            recipe["name"],
            recipe["instructions"]
        ]
        recipes_data.append(recipe_row)

        # Add ingredient rows
        for (ingredient_name, quantity, measure) in recipe["ingredients"]:
            ingredient_row = [
                ingredient_id_counter,
                recipe_id_counter,
                ingredient_name,
                quantity,
                measure
            ]
            recipe_ingredients_data.append(ingredient_row)
            ingredient_id_counter += 1

        recipe_id_counter += 1

    # 4.3 Write products.csv
    with open("products.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header row (must match the columns in generate_random_product)
        writer.writerow([
            "product_id",
            "item",
            "Departments",
            "Price",
            "Brand",
            "FulfillmentSpeed",
            "Availability",
            "WalmartCashOffers",
            "CustomerRating",
            "Form",
            "FoodCondition",
            "Flavor",
            "MeatType",
            "NutritionalContent",
            "SpecialDietNeeds",
            "PreparationMethod",
            "Container",
            "PackagedMealType",
            "Category",
            "SizeDescriptor",
            "Retailer",
            "Gifting",
            "BenefitPrograms"
        ])
        # Write each product row
        writer.writerows(products_data)

    # 4.4 Write recipes.csv
    with open("recipes.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        # columns: recipe_id, name, instructions
        writer.writerow(["recipe_id", "name", "instructions"])
        writer.writerows(recipes_data)

    # 4.5 Write recipe_ingredients.csv
    with open("recipe_ingredients.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        # columns: id, recipe_id, ingredient, quantity, measure
        writer.writerow(["id", "recipe_id", "ingredient", "quantity", "measure"])
        writer.writerows(recipe_ingredients_data)

    print(f"CSV files created:\n"
          f"  - products.csv ({len(products_data)} rows)\n"
          f"  - recipes.csv ({len(recipes_data)} rows)\n"
          f"  - recipe_ingredients.csv ({len(recipe_ingredients_data)} rows)")

if __name__ == "__main__":
    main()
# ⸻
# Note: This script generates random data for the products and recipes,
#       so the output will be different each time you run it.
#       The recipes and ingredients are fixed, but the product data is randomized.
#       You can adjust the number of products generated by changing NUM_ITEMS_TO_INSERT.
#       The CSV files will be created in the same directory as this script.
#       Make sure you have write permissions in that directory.
#       You can run this script in any Python environment.
#       If you want to run it in a Jupyter notebook, you can use the `%%writefile` magic command
#       to save the script as a .py file and then run it.
