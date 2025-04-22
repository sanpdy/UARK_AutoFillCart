import sys
import os

# # Get the absolute path to the main repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now you can import modules from agent_definitions
from recipdf_app.agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent

import asyncio
import hashlib
# import requests
import PyPDF2
import io
import streamlit as st
import uuid
import logging
import traceback
import json
# from datetime import datetime
# from components.upload import upload_panel
from recipdf_app.components.ingredient_selector import ingredient_selector_panel
# from recipdf_app.components.walmart_style import inject_walmart_style, product_card, cart_summary, walmart_navbar

# from components.cart_preview import cart_preview_panel
# --------------------------------------------------------------------
# Basic page config & Walmart-like CSS
# --------------------------------------------------------------------
st.set_page_config(page_title="ReciPDF to Walmart Cart", layout="centered", page_icon="🛒")
if "agent" not in st.session_state:
    st.session_state.agent = UnifiedCartAutofillAgent()
logging.exception("Agent failed")
st.markdown(
    """
    <style>
    /* ============ GLOBAL TYPOGRAPHY & BASE BACKGROUND ============ */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f5f5f5;           /* Light gray background for main content */
        color: #2e2e2e;                      /* Dark gray text color */
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;  /* Clean sans-serif font */
        font-size: 16px;                     /* Standard body font size */
        line-height: 1.6;                    /* Comfortable line spacing */
    }

    /* ============ SIDEBAR STYLING ============ */
    [data-testid="stSidebar"] {
        background-color: #1b1d1f;           /* Dark slate background for sidebar */
        color: #ffffff;                      /* Default text color: white */
        padding: 1rem;                       /* Sidebar padding for spacing */
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #2ea7ff;                      /* Walmart blue for sidebar headings */
        font-weight: 700;
    }

    /* ============ FORM CONTROLS IN SIDEBAR ============ */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[role="combobox"],
    .stSelectbox div[data-baseweb="select"] {
        background-color: #2a2c2f !important; /* Match dark mode theme */
        color: #ffffff !important;            /* White input text */
        border: 1px solid #444 !important;    /* Subtle gray borders */
        border-radius: 6px;
        padding: 0.5em;
    }

    /* Dropdown options styling (fix white-on-white) */
    .stSelectbox div[data-baseweb="popover"] div {
        color: #ffffff;
        background-color: #2a2c2f;
    }

    /* Slider value styling */
    .stSlider .css-1dj0hjr,
    [data-baseweb="slider"] > div > div > div {
        color: #ffffff !important;           /* Slider number labels */
    }

    /* Radio button text */
    .stRadio label {
        color: #ffffff !important;
    }

    /* Sidebar button style */
    .stButton > button {
        background-color: #0071ce;           /* Walmart blue */
        color: white;
        border-radius: 6px;
        font-weight: 600;
        font-size: 15px;
        padding: 0.5em 1.2em;
        width: 100%;                         /* Full-width button in sidebar */
    }

    .stButton > button:hover {
        background-color: #005ca6;           /* Darker blue on hover */
    }

    /* ============ TABS STYLING ============ */
    .stTabs [role="tablist"] {
        border-bottom: 2px solid #0071ce;    /* Tab bar underline */
        margin-bottom: 1rem;
    }

    .stTabs [role="tab"] {
        color: #2e2e2e;                      /* Inactive tab text */
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.75em 1.5em;
    }

    .stTabs [role="tab"][aria-selected="true"] {
        color: #0071ce;                      /* Active tab color */
        border-bottom: 4px solid #ffc220;    /* Walmart yellow underline */
        background-color: #ffffff;           /* White background for active tab */
    }

    /* ============ HEADINGS ACROSS UI ============ */
    h1 {
        color: #0071ce;                      /* Walmart blue for H1 */
        font-weight: 700;
        font-size: 2rem;
    }

    h2, .stMarkdown h2 {
        color: #333333;
        font-weight: 600;
        font-size: 1.5rem;
    }

    h3, .stMarkdown h3 {
        color: #333333;
        font-weight: 600;
        font-size: 1.25rem;
    }

    /* ============ GLOBAL INPUT FONT STYLING ============ */
    input, textarea, select {
        font-family: inherit;
        font-size: 15px !important;
    }

    /* ============ LISTS IN MARKDOWN ============ */
    ul {
        padding-left: 1.5rem;
        margin-top: 0.5rem;
    }

    li {
        margin-bottom: 0.4em;
    }

    /* ============ STATUS MESSAGES (info/success/error) ============ */
    .stAlert {
        border-radius: 8px;
        padding: 1em;
        font-size: 14px;
    }

    /* ============ FILE UPLOADER BOX ============ */
    [data-testid="stFileUploader"] section {
        background-color: #2a2c2f !important;
        color: #ffffff !important;
        border: 1px solid #444;
        border-radius: 8px;
    }

    /* ============ TEXT AREA (e.g., Paste Text) ============ */
    textarea {
        background-color: #2a2c2f !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛒 ReciPDF → Walmart Shopping Cart")

# # Theme toggle in sidebar
# st.sidebar.markdown("### Appearance")
# if "dark_mode" not in st.session_state:
#     st.session_state.dark_mode = False


# --------------------------------------------------------------------
# Light “profile” / pref store in session_state
# --------------------------------------------------------------------
st.sidebar.header("My default filters")
user = st.sidebar.text_input("Username (optional)", key="uname")
if "profiles" not in st.session_state:
    st.session_state.profiles = {}
prefs = st.session_state.profiles.setdefault(user, {}) if user else {}
mode = st.sidebar.radio("Cart generation mode:", ["Manual Mock UI", "Use Agent (AI-driven)"])
st.session_state.mode = mode
# ------------------------------------------------------------------#
# Compact preference panel (sidebar) – stored in session_state
# ------------------------------------------------------------------#
# Define users preferences as a dictionary
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
# Dynamically render sidebar fields
st.sidebar.markdown("### Product Filters")

for field, field_info in PREFERENCE_FIELDS.items():
    field_type = field_info[0]
    default_value = prefs.get(field, field_info[1] if field_type == "text" else field_info[1][-1])

    if field_type == "slider":
        min_val, max_val, default = field_info[1]
        prefs[field] = st.sidebar.slider(field, min_val, max_val, prefs.get(field, default))
    elif field_type == "select":
        options = field_info[1]
        prefs[field] = st.sidebar.selectbox(field, options, index=options.index(prefs.get(field, options[0])))
    elif field_type == "text":
        prefs[field] = st.sidebar.text_input(field, value=default_value)

if st.sidebar.button("Save prefs"):
    st.session_state.profiles[user] = prefs
    st.sidebar.success("Saved (session only)")

# Initialize session state
if "parsed_ingredients" not in st.session_state:
    st.session_state.parsed_ingredients = []

if "matched_products" not in st.session_state:
    st.session_state.matched_products = []

# PHASE 1: Upload + Extract
# upload_panel()

# PHASE 2: Match to Walmart products
if st.session_state.parsed_ingredients:
    ingredient_selector_panel()

# PHASE 3: Cart preview
# if st.session_state.matched_products:
#     cart_preview_panel()

# --------------------------------------------------------------------
# 2. Caching the PDF Parsing
#    We'll create a function to parse a PDF using PyPDF2.
#    @st.cache_data ensures we only re-parse if the file changes.
# --------------------------------------------------------------------
@st.cache_data
def parse_pdf_file(file_bytes: bytes) -> str:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text_chunks = []
    for page in pdf_reader.pages:
        text_chunks.append(page.extract_text())
    return "\n".join(text_chunks)

# ------------------------------------------------------------------#
# 3 .   UI divided in two tabs – avoids needless work
# ------------------------------------------------------------------#
if mode == "Use Agent (AI-driven)":
    tab_recipe, tab_cart = st.tabs(["📄 Upload", "🧾 Cart"])
else:
    tab_recipe, tab_search, tab_cart = st.tabs(["📄 Upload", "🔎 Search", "🧾 Cart"])

# ──────────────────────────────────────────────────────────────────
with tab_recipe:
    st.subheader("Upload recipe (PDF or TXT)")
    up = st.file_uploader("Choose file", type=["pdf", "txt"])
    paste_text = st.text_area("Or paste recipe text below")

    recipe_text = ""
    if up:
        data = up.read()
        key = hashlib.md5(data).hexdigest()  # fingerprint for cache

        if up.type == "application/pdf":
            recipe_text = parse_pdf_file(data)  # cached
        else:
            recipe_text = data.decode(errors="ignore")

    elif paste_text.strip():
        recipe_text = paste_text

    if recipe_text:
        st.text_area("Recipe text", recipe_text, height=200)

        ing_lines = [
            ln.strip()
            for ln in recipe_text.splitlines()
            if "ingredient" in ln.lower()
        ]
        if ing_lines:
            st.write("**Detected ingredient lines**")
            st.write("\n".join(f"- {l}" for l in ing_lines))
        else:
            st.info("No obvious ingredient headings detected.")

        if st.button("Extract Ingredients"):
            if not isinstance(recipe_text, str) or not recipe_text.strip():
                st.error("Recipe text is empty or invalid.")
                st.stop()  # important: stop here to prevent further execution

            # Clear matched product and previous selections
            st.session_state.matched_products = []

            # Reset previous radio button keys
            for idx, item in enumerate(st.session_state.get('parsed_ingredients', [])):
                k = f"sel_{idx}_{item['ingredient'].replace(' ', '_')}"
                if k in st.session_state:
                    del st.session_state[k]

            with st.spinner("Making good choices..."):
                try:
                    result_raw = asyncio.run(st.session_state.agent.get_cart_from_recipe(recipe_text))

                    
                    # ✅ Expect a dict. Don't parse as JSON.
                    if not isinstance(result_raw, dict) or "url" not in result_raw:
                        raise ValueError("Agent did not return expected cart response.")
                    else:
                        result = result_raw
                    # Try parsing it if it's a string
                    # if isinstance(result_raw, str):
                    #     try:
                    #         result = json.loads(result_raw)
                    #     except json.JSONDecodeError as e:
                    #         st.error(f"Failed to parse result JSON: {e}")
                    #         st.code(result_raw)
                    #         st.stop()
                    # else:
                    #     result = result_raw

                    st.session_state.cart_url = result["url"]
                    st.session_state.cart_items = result.get("items", [])
                    st.session_state.cart_summary = result.get("summary", "")

                    st.success("Cart generated successfully!")

                except Exception as e:
                    st.error(f"Agent error: {e}")
                    st.code(traceback.format_exc())
    # -------------------------------------------
    # 🛒 Add Walmart Match UI once ingredients exist
    # -------------------------------------------
    if st.session_state.mode == "Manual Mock UI" and st.session_state.get("parsed_ingredients"):
        st.markdown("---")
        st.header("2. Match Ingredients to Walmart Products")

        cols = st.columns(2)
        with cols[0]:
            # Step 1: Loop over ingredients and show radio selectors
            for idx, item in enumerate(st.session_state.parsed_ingredients):
                with st.expander(f"🧾 {item['ingredient']} ({item['quantity']})"):
                    selected = st.radio(
                        f"Select product for {item['ingredient']}",
                        [
                            f"GV {item['ingredient'].title()} - $2.99",
                            f"Organic {item['ingredient']} - $3.49"
                        ],
                        key=f"sel_{idx}_{item['ingredient'].replace(' ', '_')}"
                    )
                    rationale = "Best price for quantity." if 'GV' in selected else "Organic preference."
                    st.text(f"Reason: {rationale}")

            # ✅ Step 2: ONE button, outside the loop, with a stable key
            if st.button("Confirm Matches", key="confirm_matches_button"):
                matched = []
                for idx, item in enumerate(st.session_state.parsed_ingredients):
                    choice = st.session_state.get(f"sel_{idx}_{item['ingredient'].replace(' ', '_')}")
                    if choice:
                        matched.append({
                            "name": choice.split(" - ")[0],
                            "itemId": uuid.uuid4().int >> 96,
                            "price": float(choice.split(" - $")[-1])
                        })
                st.session_state.matched_products = matched
                st.success("Products selected.")

# ──────────────────────────────────────────────────────────────────
if mode != "Use Agent (AI-driven)":
    with tab_search:
        st.subheader("Quick Walmart field search (mock)")

        # put widgets inside a form ⇒ app re‑runs only on Submit
        with st.form("search"):
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
                        {"name": f"Mock Product for {value}","itemId": 46491801,  "price": 2.99},
                        {"name": f"Another Mock {value} Product","itemId": 10452368, "price": 3.49}
                    ]
                }
            )   
            st.success("Data fetched (mock). Integrate your real API key for live results!")
# ──────────────────────────────────────────────────────────────────
with tab_cart:
    if st.session_state.mode == "Use Agent (AI-driven)" and st.session_state.get("cart_url"):
        st.subheader("3. Cart Preview & Export")
    
        url = st.session_state.cart_url
        st.text_input("Cart URL", value=url)
        st.markdown(f"[Open in Walmart Cart]({url})")

# with tab_cart:
#     if st.session_state.get("cart_items"):
#         st.subheader("Your Cart")
#         for item in st.session_state.cart_items:
#             product_card(
#                 name=item.get("name", "Unnamed"),
#                 price=item.get("price", 0.0),
#                 description="Auto-selected by recipe agent",
#                 rating=item.get("rating", 4.0)
#             )
#         cart_summary(st.session_state.cart_items)
    # Mock setup
    # if st.session_state.get("matched_products"):
    #     st.subheader("3. Cart Preview & Export")
    #     total = 0.0
    #     for item in st.session_state.matched_products:
    #         st.markdown(f"- **{item['name']}** — ${item['price']}")
    #         total += item['price']

    #     st.markdown(f"**Total:** ${total:.2f}")

    #     ids = ",".join(str(item['itemId']) for item in st.session_state.matched_products)
    #     url = f"https://affil.walmart.com/cart/addToCart?items={ids}"

    #     st.text_input("Cart URL", value=url)
    #     st.markdown(f"[Open in Walmart Cart]({url})")

# --------------------------------------------------------------------
# 5. User Preferences (Sliders / Selectboxes)
# --------------------------------------------------------------------
# st.header("Set & Save Your Walmart Attribute Preferences")

# if username:
#     if "field_values" not in user_prefs:
#         user_prefs["field_values"] = {}

#     preference_fields = {
#         "Price": ("slider", (0.0, 100.0, 20.0)),       # (min, max, default)
#         "CustomerRating": ("slider", (0.0, 5.0, 4.0)),
#         "FulfillmentSpeed": ("select", ["Same Day", "Next Day", "Two Day", "Standard"]),
#         "Availability": ("select", ["In Stock", "Out of Stock", "Limited Stock"]),
#         "Brand": ("text", ""),
#         "Container": ("select", ["N/A", "Box", "Bag", "Bottle", "Carton", "Jar"]),
#         "Form": ("select", ["N/A", "Whole", "Sliced", "Powder", "Liquid", "Granulated"]),
#         "Departments": ("text", "Grocery"),
#         "Category": ("text", ""),
#         "MeatType": ("select", ["N/A", "Chicken", "Beef", "Pork", "Turkey", "Fish", "Seafood"]),
#         "SpecialDietNeeds": ("select", ["None", "Gluten-Free", "Vegan", "Keto-Friendly", "Organic", "Vegetarian"]),
#     }

#     st.write("Use these controls to set default preferences.")

#     for field_name, field_type_info in preference_fields.items():
#         control_type = field_type_info[0]
#         if control_type == "slider":
#             min_val, max_val, default_val = field_type_info[1]
#             current_value = user_prefs["field_values"].get(field_name, default_val)
#             slider_val = st.slider(
#                 field_name,
#                 min_value=min_val,
#                 max_value=max_val,
#                 value=float(current_value),
#                 step=0.1,
#             )
#             user_prefs["field_values"][field_name] = slider_val

#         elif control_type == "select":
#             options = field_type_info[1]
#             stored_val = user_prefs["field_values"].get(field_name, options[0])
#             if stored_val not in options:
#                 stored_val = options[0]
#             select_val = st.selectbox(field_name, options, index=options.index(stored_val))
#             user_prefs["field_values"][field_name] = select_val

#         elif control_type == "text":
#             default_text = field_type_info[1] if len(field_type_info) > 1 else ""
#             current_text = user_prefs["field_values"].get(field_name, default_text)
#             text_val = st.text_input(field_name, value=current_text)
#             user_prefs["field_values"][field_name] = text_val

#     # Save/Load Buttons
#     st.write("---")
#     if st.button("Save Preferences"):
#         st.success("Preferences saved (in memory).")

#     if st.button("Load Preferences"):
#         st.info("Preferences reloaded from session state.")
#         st.experimental_rerun()

#     # Display Current Values
#     st.subheader("Current Preference Values")
#     st.json(user_prefs["field_values"])

#     # Simulate a search with these preferences
#     if st.button("Simulate a Walmart API Search Using My Preferences"):
#         brand_filter = user_prefs["field_values"].get("Brand", "")
#         max_price = user_prefs["field_values"].get("Price", 20.0)
#         min_rating = user_prefs["field_values"].get("CustomerRating", 0.0)
#         st.write(f"**Simulating** with brand='{brand_filter}', price<={max_price}, rating>={min_rating}")
#         mock_data = {
#             "search_query": brand_filter,
#             "price_limit": max_price,
#             "min_rating": min_rating,
#             "results": [
#                 {"itemName": "Mock Pref Product 1", "price": 19.99, "rating": 4.2},
#                 {"itemName": "Mock Pref Product 2", "price": 9.99, "rating": 4.0},
#             ]
#         }
#         st.json(mock_data)

# else:
#     st.info("Enter a username above to enable saving/loading preferences.")
