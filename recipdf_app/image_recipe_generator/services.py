import os
import requests
import tempfile
from openai import OpenAI
from transformers import pipeline as hf_pipeline

# Image classifier (cached as a module‐level singleton)
_dish_classifier = None
def get_dish_classifier():
    global _dish_classifier
    if _dish_classifier is None:
        _dish_classifier = hf_pipeline(
            "image-classification",
            model="eslamxm/vit-base-food101",
        )
    return _dish_classifier

def classify_dish(image_bytes, suffix):
    """Save to temp file, run classification, return (label, score)."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(image_bytes); tmp.flush()
    results = get_dish_classifier()(tmp.name)
    os.unlink(tmp.name)
    top = results[0]
    return top["label"], top["score"]

# Spoonacular lookup
def find_recipes(label, number=10):
    key = os.getenv("SPOONACULAR_API_KEY")
    resp = requests.get(
        "https://api.spoonacular.com/recipes/complexSearch",
        params={"apiKey": key, "query": label, "number": number}
    )
    return resp.json().get("results", [])

def get_ingredient_list(recipe_id):
    key = os.getenv("SPOONACULAR_API_KEY")
    resp = requests.get(
        f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json",
        params={"apiKey": key}
    )
    data = resp.json().get("ingredients", [])
    return [
        {
            "name": i["name"],
            "amount": i["amount"]["metric"]["value"],
            "unit": i["amount"]["metric"]["unit"],
        }
        for i in data
    ]

# OpenAI helper to pick best title
def pick_best_recipe(titles, label, confidence):
    client = OpenAI()
    system = {"role":"system","content":"You are a culinary assistant."}
    user = {
        "role":"user",
        "content": f"Predicted '{label}' ({confidence:.2f}). Which title matches best? {titles}"
    }
    choice = client.chat.completions.create(
        model="gpt-4", messages=[system, user], temperature=0
    ).choices[0].message.content.strip().strip('"\'')
    return choice

# Agent cart generator
def generate_cart_url(recipe_text):
    from recipdf_app.agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent
    agent = UnifiedCartAutofillAgent()
    return agent.get_cart_from_recipe(recipe_text)
