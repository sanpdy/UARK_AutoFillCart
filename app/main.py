# app/main.py

import streamlit as st
from modules.nlp_extractor import extract_items
from modules.walmart_integration import add_items_to_walmart_cart

def main():
    st.title("UARK AutoFillCart")

    query = st.text_input("Enter your shopping list (e.g., eggs, milk):")

    if query:
        st.write("Processing your query...")
        items = [item.strip() for item in query.split(",") if item.strip()]

        st.subheader("Draft Cart Items")
        for item in items:
            st.write(f"- {item}")

        if st.button("Add These Items to Walmart Cart"):
            st.write("Attempting to add items to Walmart cart...")
            result = add_items_to_walmart_cart(items)
            st.write("Results:")
            for item, status in result.items():
                status_text = "Success" if status else "Failed"
                st.write(f"- {item}: {status_text}")

if __name__ == "__main__":
    main()
