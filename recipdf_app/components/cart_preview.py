import streamlit as st

def cart_preview_panel():
    st.header("3. Cart Preview & Export")

    total = 0.0
    for item in st.session_state.matched_products:
        st.markdown(f"- **{item['name']}** — ${item['price']}")
        total += item['price']

    st.markdown(f"**Total:** ${total:.2f}")

    ids = ",".join(str(item['itemId']) for item in st.session_state.matched_products)
    url = f"https://affil.walmart.com/cart/addToCart?items={ids}"

    st.text_input("Cart URL", value=url)
    st.markdown(f"[Open in Walmart Cart]({url})")