# Streamlit app: upload dish image -> identify dish -> auto-select best recipe via LLM -> generate Walmart cart URL with ingredients only

import os
import tempfile
import asyncio
import streamlit as st
import requests
import load_env

from transformers import pipeline as hf_pipeline
from openai import OpenAI
from agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent

st.set_page_config(page_title="AI Recipe to Walmart Cart", layout="centered")
st.title("🍲 Photo→Recipe→Cart (Auto-Select)")
st.write("Upload a dish photo; the app will identify it, auto-select the best recipe via an LLM, and cart the ingredients.")

oai_key = os.getenv("OPENAI_API_KEY")
if not oai_key:
    raise RuntimeError("OPENAI_API_KEY is missing in the environment.")
client = OpenAI()

dish_classifier = hf_pipeline(
    "image-classification",
    model="eslamxm/vit-base-food101",
)

image_file = st.file_uploader("Upload Dish Image", type=["png", "jpg", "jpeg"] )

if image_file and st.button("Process Image → Cart" ):
    # Classify the dish image
    st.info("Identifying dish from image...")
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.name)[1])
    tmp_img.write(image_file.getvalue())
    tmp_img.flush()
    results = dish_classifier(tmp_img.name)
    os.unlink(tmp_img.name)
    print(f"[DEBUG] Classification results: {results}")
    dish_label = results[0].get("label", "Unknown")
    confidence = results[0].get("score", 0)
    st.success(f"Predicted dish: **{dish_label}** (confidence {confidence:.2f})")

    # Fetch top 5 recipe options via Spoonacular API
    spoon_key = os.getenv("SPOONACULAR_API_KEY")
    if not spoon_key:
        st.error("Missing SPOONACULAR_API_KEY in environment.")
        st.stop()

    st.info("Searching Spoonacular for recipes...")
    search_url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": spoon_key,
        "query": dish_label,
        "number": 10,
        "instructionsRequired": False
    }
    print(f"Spoonacular search params: {params}")
    resp = requests.get(search_url, params=params)
    data = resp.json()
    print(f"Spoonacular search response: {data}")
    results = data.get("results", [])
    if not results:
        st.error("No recipes found for this dish.")
        st.stop()

    # OpenAI to pick the best recipe
    titles = [r.get("title", "Untitled") for r in results]
    system_msg = {"role": "system", "content": "You are a culinary assistant. Choose the recipe title that best matches the dish label and confidence provided."}
    user_msg = {"role": "user", "content": f"Image classification predicted '{dish_label}' with confidence {confidence:.2f}. Here are recipe options: {titles}. Return only the best title exactly as shown without any extra quotes."}
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[system_msg, user_msg],
        temperature=0.0
    )

    raw_choice = response.choices[0].message.content.strip()
    choice = raw_choice.strip('"\'')
    print(f"OpenAI selected recipe (raw): {raw_choice}")
    st.info(f"Auto-selected recipe: **{choice}**")

    matched = next((r for r in results if r.get("title") == choice), None)
    if not matched:
        matched = results[0]
        st.warning("LLM choice not found or misformatted; defaulting to first recipe.")
        choice = matched.get("title")
    recipe_id = matched.get("id")

    # Ingredients for the recipe
    st.info(f"Fetching ingredients for '{choice}'...")
    info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json"
    info_params = {"apiKey": spoon_key}
    print(f"[DEBUG] Spoonacular ingredient request: URL={info_url}, params={info_params}")
    info_resp = requests.get(info_url, params=info_params)
    ingr_data = info_resp.json()
    print(f"[DEBUG] Spoonacular ingredient response: {ingr_data}")

    st.markdown(f"### Ingredients for **{choice}**")
    ingredient_list = []
    for item in ingr_data.get('ingredients', []):
        name = item.get('name')
        amt = item.get('amount', {}).get('metric', {}).get('value')
        unit = item.get('amount', {}).get('metric', {}).get('unit')
        ingredient_list.append({'name': name, 'amount': amt, 'unit': unit})
        text = f"{amt} {unit} {name}" if amt and unit else name
        st.write(f"- {text}")

    recipe_text = choice + "\n\nIngredients:\n" + "\n".join(
        [f"{i['amount']} {i['unit']} {i['name']}" for i in ingredient_list]
    )
    st.info("Generating Walmart cart URL...")
    agent = UnifiedCartAutofillAgent()
    cart_url = asyncio.run(agent.get_cart_from_recipe(recipe_text, verbose=False))
    st.success("🛒 Cart URL ready!")
    st.markdown(f"[Open Your Walmart Cart]({cart_url})")

# Requirements:
# pip install streamlit transformers torch requests pdfminer.six openai
# run: streamlit run vision_pipeline.py
