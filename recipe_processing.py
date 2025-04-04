import json
import tkinter as tk
from tkinter import filedialog
from pdfminer.high_level import extract_text

from agent_definitions.agents.ingredient_extractor_agent import IngredientExtractorAgent
from utils.pdf_to_txt_util import replace_fractions

if __name__ == "__main__":
    # Initialize Tkinter and hide the main window.
    root = tk.Tk()
    root.withdraw()

    # Open a file explorer dialog to select a file (txt, md, or pdf).
    file_path = filedialog.askopenfilename(
        title="Select a Recipe File",
        filetypes=[("Recipe Files", ("*.txt", "*.md", "*.pdf"))]
    )

    if file_path:
        recipe = ""
        # Check file extension to decide how to read the file.
        if file_path.lower().endswith(".pdf"):
            if extract_text is None:
                print("pdfminer.six is required to process PDF files. Please install it using 'pip install pdfminer.six'")
                exit(1)
            # Extract text from the PDF and process fractions.
            recipe = extract_text(file_path)
            recipe = replace_fractions(recipe)
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                recipe = file.read()

        # Use the recipe text as input for the ingredient extraction agent.
        agent = IngredientExtractorAgent()
        ingredients = agent.extract_ingredients_from_recipe(recipe)
        print(json.dumps(ingredients, indent=2))
    else:
        print("No file selected.")

# if __name__ == "__main__":
#     # Initialize Tkinter and hide the main window.
#     root = tk.Tk()
#     root.withdraw()
#
#     # Open a file explorer dialog to select a .txt file.
#     file_path = filedialog.askopenfilename(
#         title="Select a Recipe Text File",
#         filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md")]
#     )
#
#     if file_path:
#         with open(file_path, "r", encoding="utf-8") as file:
#             recipe = file.read()
#
#         agent = IngredientExtractorAgent()
#         ingredients = agent.extract_ingredients_from_recipe(recipe)
#         print(json.dumps(ingredients, indent=2))
#     else:
#         print("No file selected.")