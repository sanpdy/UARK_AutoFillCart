import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from recipdf_app.agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent
import asyncio
import hashlib
import PyPDF2
import io
import streamlit as st
import uuid
import logging
import traceback
import json
import tempfile
import requests
from openai import OpenAI

from recipdf_app.image_recipe_generator.services import (
    classify_dish,
    find_recipes,
    get_ingredient_list,
    pick_best_recipe,
    generate_cart_url,
)

try:
    from transformers import pipeline as hf_pipeline
except ImportError:
    st.error("Please install transformers: pip install transformers torch")


st.set_page_config(page_title="ReciPDF to Walmart Cart", layout="centered", page_icon="🛒")
if "agent" not in st.session_state:
    st.session_state.agent = UnifiedCartAutofillAgent()

st.markdown(
    """
    <style>
    /* Walmart brand colors */
    :root {
        --walmart-blue: #0071ce;
        --walmart-yellow: #ffc220;
        --walmart-black: #333333;
        --walmart-light-gray: #f8f8f8;
        --walmart-medium-gray: #e6e6e6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--walmart-blue) !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: white !important;
    }

     .stMarkdown, .stExpanderContent {
        text-align: center !important;
    }
    
    /* Main app styling */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--walmart-light-gray) !important;
        color: var(--walmart-black) !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--walmart-blue) !important;
        font-weight: bold !important;
    }
    
    /* Main title styling */
    .stTitleContainer h1 {
        color: var(--walmart-blue) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        text-align: center !important;

    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] section {
        background-color: var(--walmart-blue) !important;
        border-radius: 8px !important;
        border: 2px solid var(--walmart-blue) !important;
        padding: 20px !important;
        color: var(--walmart-light-gray) !important;
    
    }
    .stsuccess {
            background-color: var(--walmart-yellow);  !important;  /* light green */
            color: var(--walmart-blue);  /* dark green text */
            border-left:     4px solid #28a745 !important; /* bright green accent */
        }
    
    [data-testid="stTextArea"] label {
    color: var(--walmart-black) !important;
}

    [data-testid="stTextArea"] textArea {
    background-color: var(--walmart-light-gray) !important;
    color: var(--walmart-black) !important;
    cursor: text !important;
    caret-color: var(--walmart-blue) !important;
    border: 1px solid var(--walmart-medium-gray) !important;}

    
    [data-testid="stFileUploader"] section p {
        color: var(--walmart-light-gray) !important;
    }

    /* Buttons */
    button, [data-testid="stButton"] button {
        background-color: var(--walmart-blue) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 20px !important;
        padding: 0.5rem 1.5rem !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    button:hover, [data-testid="stButton"] button:hover {
        background-color: #005da6 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* File uploader button */
    [data-testid="stFileUploader"] button {
        background-color: var(--walmart-yellow) !important;
        color: var(--walmart-black) !important;
    }
    
    /* Tabs styling */
    .stTabs [role="tab"] {
        color: var(--walmart-black) !important;
        font-weight: 600 !important;
        background-color: var(--walmart-medium-gray) !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 0.5rem 1rem !important;
        margin-right: 2px !important;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        background-color: var(--walmart-blue) !important;
        color: white !important;
    }
    
    /* Text input styling */
    input[type="text"] {
        border: 1px solid var(--walmart-medium-gray) !important;
        border-radius: 4px !important;
        padding: 8px !important;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: rgba(0, 113, 206, 0.1) !important;
        border-left-color: var(--walmart-blue) !important;
    }
    
    /* Walmart cart button */
    .walmart-cart-btn {
        display: block;
        background-color: var(--walmart-blue);
        color: white !important;
        text-decoration: none;
        padding: 15px 30px;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        margin: 30px auto;
        max-width: 300px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .walmart-cart-btn:hover {
        background-color: #005da6;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        text-decoration: none;
    }
    
    /* Decoration elements */
    [data-testid="stDecoration"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("ReciPDF")

# --------------------------------------------------------------------
# Sidebar: user preferences
# --------------------------------------------------------------------
st.sidebar.header("My default filters")
user = st.sidebar.text_input("Username (optional)", key="uname")
if "profiles" not in st.session_state:
    st.session_state.profiles = {}
prefs = st.session_state.profiles.setdefault(user, {}) if user else {}
mode = st.sidebar.radio(
    "Cart generation mode:",
    ["Manual Mock UI", "Use Agent (AI-driven)"],
)
st.session_state.mode = mode

PREFERENCE_FIELDS = {
    "Price": ("slider", (0.0, 100.0, 25.0)),
    "CustomerRating": ("slider", (0.0, 5.0, 4.0)),
    "FulfillmentSpeed": ("select", ["Same Day", "Next Day", "Two Day", "Standard"]),
    "Availability": ("select", ["In Stock", "Out of Stock", "Limited Stock"]),
    "Brand": ("text", ""),
    "Category": ("text", ""),
    "Form": ("select", ["N/A", "Whole", "Sliced", "Powder", "Liquid", "Granulated"]),
    "Container": ("select", ["N/A", "Box", "Bag", "Bottle", "Carton", "Jar"]),
    "MeatType": ("select", ["N/A", "Chicken", "Beef", "Pork", "Turkey", "Fish", "Seafood"]),
    "SpecialDietNeeds": ("select", ["None", "Vegan", "Gluten-Free", "Keto-Friendly", "Organic", "Vegetarian"]),
}
st.sidebar.markdown("### Product Filters")
for field, field_info in PREFERENCE_FIELDS.items():
    ftype, info = field_info
    if ftype == "slider":
        minv, maxv, default = info
        prefs[field] = st.sidebar.slider(field, minv, maxv, prefs.get(field, default))
    elif ftype == "select":
        opts = info
        prefs[field] = st.sidebar.selectbox(field, opts, index=opts.index(prefs.get(field, opts[0])))
    else:
        prefs[field] = st.sidebar.text_input(field, value=prefs.get(field, info))

if st.sidebar.button("Save prefs"):
    st.session_state.profiles[user] = prefs
    st.sidebar.success("Saved (session only)")


# --------------------------------------------------------------------
# Caching the PDF Parsing
# --------------------------------------------------------------------
@st.cache_data
def parse_pdf_file(file_bytes: bytes) -> str:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text_chunks = [page.extract_text() for page in pdf_reader.pages]
    return "\n".join(text_chunks)


# --------------------------------------------------------------------
# UI divided in tabs
# --------------------------------------------------------------------
if mode == "Use Agent (AI-driven)":
    tab_recipe, tab_cart = st.tabs([" Upload Recipe", "🧾 Cart"])
else:
    tab_recipe, tab_cart = st.tabs(["  Upload Recipe  ", "  Cart  "])

with tab_recipe:
    col1, col2 = st.columns(2)

    # --- Text/PDF path ---
    with col1:
        st.markdown("### Recipe")
        up = st.file_uploader("Choose PDF or TXT file", type=["pdf", "txt"])
        paste_text = st.text_area("Or paste recipe text below")

    # --- Image path ---
    with col2:
        st.markdown("### Image")
        image_file = st.file_uploader(
            "Upload dish image", type=["png", "jpg", "jpeg"], key="image_upload"
        )
        if image_file:
            st.image(image_file, use_container_width=True)

            # 1) Identify & fetch recipe
            if st.button("Identify Dish & Find Recipe", key="process_image"):
                # classify the dish
                lbl, conf = classify_dish(
                    image_file.getvalue(),
                    os.path.splitext(image_file.name)[1]
                )
                dish_label = lbl.replace("_", " ").title()
                st.success(f"Predicted dish: **{dish_label}** (confidence {conf:.2f})")

                # find recipes
                recipes = find_recipes(dish_label)
                if recipes:
                    titles = [r["title"] for r in recipes]
                    if st.session_state.get("openai_client"):
                        choice = pick_best_recipe(titles, lbl, conf)
                    else:
                        choice = titles[0]
                    matched = next(r for r in recipes if r["title"] == choice)

                    # build ingredient list & recipe text
                    ingredients = get_ingredient_list(matched["id"])
                    recipe_text = (
                        choice + "\n\nIngredients:\n"
                        + "\n".join(
                            f"{i['amount']} {i['unit']} {i['name']}"
                            if i["amount"] and i["unit"] else i["name"]
                            for i in ingredients
                        )
                    )

                    # persist for the next run
                    st.session_state.recipe_data = {
                        "title": choice,
                        "ingredients": ingredients,
                        "recipe_text": recipe_text,
                    }
                    st.session_state.recipe_text = recipe_text
                    st.success(f"Found recipe: **{choice}**")

            # 2) Generate cart
            if st.session_state.get("recipe_data"):
                rd = st.session_state.recipe_data
                st.success(f"Ready to generate cart for **{rd['title']}**")
                if st.button("Generate Cart from This Recipe", key="generate_cart"):
                    with st.spinner("Creating Walmart cart..."):
                        resp = asyncio.run(
                            generate_cart_url(st.session_state.recipe_text)
                        )
                        st.session_state.cart_url     = resp.get("url")
                        st.session_state.cart_items   = resp.get("items", [])
                        st.session_state.cart_summary = resp.get("summary", "")
                        st.success("Cart generated successfully!")


    st.markdown("---")

    # --- PDF/Text processing ---
    recipe_text = ""
    if up:
        data = up.read()
        if up.type == "application/pdf":
            recipe_text = parse_pdf_file(data)
        else:
            recipe_text = data.decode(errors="ignore")
    elif paste_text.strip():
        recipe_text = paste_text

    if recipe_text:
        st.markdown("### Recipe Text")
        st.text_area("Extracted text", recipe_text, height=200)
        if st.button("Extract Ingredients & Generate Cart", key="text_process"):
            with st.spinner("Processing recipe and generating cart..."):
                try:
                    result_raw = asyncio.run(st.session_state.agent.get_cart_from_recipe(recipe_text))
                    if not isinstance(result_raw, dict) or "url" not in result_raw:
                        raise ValueError("Agent did not return expected cart response.")
                    st.session_state.cart_url = result_raw["url"]
                    st.session_state.cart_items = result_raw.get("items", [])
                    st.session_state.cart_summary = result_raw.get("summary", "")
                    st.success("Cart generated successfully!")
                except Exception as e:
                    st.error(f"Agent error: {e}")
                    st.code(traceback.format_exc())


# --- Cart tab ---
with tab_cart:
    if st.session_state.get("cart_url"):
        st.subheader("Your Walmart Cart")
        url = st.session_state.cart_url
        st.text_input("Cart URL", value=url)
        st.markdown(f"""
            <div style="display: flex; justify-content: center; margin: 20px 0;">
                <a href="{url}" target="_blank" style="...">🛒 Open in Walmart Cart</a>
            </div>
        """, unsafe_allow_html=True)

commented ="""if mode != "Use Agent (AI-driven)":
    with tab_search:
        st.subheader("Quick Walmart field search (mock)")
        with st.form("search_form"):
            field = st.selectbox(
                "Field",
                [
                    "product_id", "itemid", "Brand", "Price", "CustomerRating",
                    "Category", "Availability",
                ],
            )
            value = st.text_input("Value / query")
            submitted = st.form_submit_button("Search")

        if submitted and value:
            st.success("Mock query executed – plug API key for live data")
            st.json(
                {
                    "field": field,
                    "value": value,
                    "items": [
                        {"name": f"Mock Product for {value}", "itemId": 46491801,  "price": 2.99},
                        {"name": f"Another Mock {value} Product", "itemId": 10452368, "price": 3.49}
                    ]
                }
            )
            st.success("Data fetched (mock). Integrate your real API key for live results!")
"""

