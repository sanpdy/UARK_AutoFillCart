import streamlit as st

def upload_panel():
    st.header("1. Upload Recipe & Extract Ingredients")
    uploaded_file = st.file_uploader("Upload recipe (PDF or TXT)", type=["pdf", "txt"])
    paste_text = st.text_area("Or paste recipe text below")

    if st.button("Extract Ingredients"):
        # Stub logic: pretend we parsed ingredients
        st.session_state.parsed_ingredients = [
            {"ingredient": "green bell pepper", "quantity": "1 large", "prep": "sliced"},
            {"ingredient": "swiss cheese", "quantity": "4 slices", "prep": ""},
        ]
        st.success("Ingredients extracted.")