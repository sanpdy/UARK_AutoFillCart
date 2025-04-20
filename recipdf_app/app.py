import hashlib
import requests
import PyPDF2
import io
import streamlit as st
from datetime import datetime

# --------------------------------------------------------------------
# Basic page config & Walmart-like CSS
# --------------------------------------------------------------------
st.set_page_config("Walmart Recipe 🛒", layout="centered", page_icon="🛒")
st.markdown(
    """
    <style>
      h1 {color:#007dc6;}
      .stButton>button {background:#007dc6;color:#fff;border:none;border-radius:4px;}
      [data-testid=stHeader] {background:#007dc6;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Walmart‑style Recipe & Product Quick Prototype")

# --------------------------------------------------------------------
# 1.  Light “profile” / pref store in session_state
# --------------------------------------------------------------------
if "profiles" not in st.session_state:
    st.session_state.profiles = {}

user = st.sidebar.text_input("Username (optional)", key="uname")
prefs = st.session_state.profiles.setdefault(user, {}) if user else {}

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
tab_recipe, tab_search = st.tabs(["📄  Recipe upload", "🔎  Walmart search"])

# ──────────────────────────────────────────────────────────────────
with tab_recipe:
    st.subheader("Upload recipe (PDF or TXT)")
    up = st.file_uploader("Choose file", type=["pdf", "txt"])

    if up:
        data = up.read()
        key = hashlib.md5(data).hexdigest()            # fingerprint for cache

        if up.type == "application/pdf":
            recipe_text = parse_pdf_file(data)  # cached
        else:
            recipe_text = data.decode(errors="ignore")

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

# ──────────────────────────────────────────────────────────────────
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
                    {"itemId": 123456, "name": f"Mock Product for {value}", "salePrice": 3.99},
                    {"itemId": 789012, "name": f"Another Mock {value} Product", "salePrice": 5.49}
                ]
            }
        )   
    st.success("Data fetched (mock). Integrate your real API key for live results!")

# ------------------------------------------------------------------#
# 4 .   Compact preference panel (sidebar) – stored in session_state
# ------------------------------------------------------------------#
with st.sidebar:
    st.header("My default filters")
    price = st.slider("Max price", 0.0, 100.0, prefs.get("price", 25.0))
    rating = st.slider("Min rating", 0.0, 5.0, prefs.get("rating", 4.0))
    diet  = st.selectbox(
        "Diet",
        ["None", "Vegan", "Gluten‑Free", "Keto"],
        index=["None", "Vegan", "Gluten‑Free", "Keto"].index(prefs.get("diet", "None")),
    )

    if st.button("Save prefs"):
        prefs.update(price=price, rating=rating, diet=diet)
        st.success("Saved (session only)")


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
