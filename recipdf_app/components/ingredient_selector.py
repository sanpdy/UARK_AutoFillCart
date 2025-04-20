import streamlit as st

def ingredient_selector_panel():
    st.header("2. Match Ingredients to Walmart Products")

    cols = st.columns(2)
    with cols[0]:
        for idx, item in enumerate(st.session_state.parsed_ingredients):
            with st.expander(f"🧾 {item['ingredient']} ({item['quantity']})"):
                selected = st.radio(f"Select product for {item['ingredient']}", 
                                    [f"GV {item['ingredient'].title()} - $2.99", f"Organic {item['ingredient']} - $3.49"],
                                    key=f"sel_{idx}")
                rationale = f"Best price for quantity." if 'GV' in selected else "Organic preference."
                st.text(f"Reason: {rationale}")

    if st.button("Confirm Matches"):
        st.session_state.matched_products = [
            {"name": "GV Green Bell Pepper", "itemId": 46491801, "price": 2.99},
            {"name": "GV Swiss Cheese", "itemId": 10452368, "price": 3.49},
        ]
        st.success("Products selected.")