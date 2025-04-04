import json
from recipe_processing import import_file_and_extract_ingredients

print("Running UARK_AutoFillCart as a module!")

if __name__ == "__main__":
    ingredients = import_file_and_extract_ingredients()
    print(json.dumps(ingredients, indent=2))
