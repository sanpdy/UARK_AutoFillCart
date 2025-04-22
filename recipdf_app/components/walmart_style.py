# 🧩 walmart_style.py – Walmart-Styled Components

import streamlit as st

def inject_walmart_style():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f5f5f5;
            color: #2e2e2e;
            font-family: "Helvetica Neue", sans-serif;
        }

        .stButton>button {
            background-color: #0071ce;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.6em 1.2em;
            font-weight: 600;
            transition: background 0.2s ease;
        }

        .stButton>button:hover {
            background-color: #005ca6;
        }

        h1 { color: #0071ce; font-weight: 700; }
        h2, h3 { color: #444; font-weight: 600; }

        .stTabs [role="tablist"] {
            border-bottom: 2px solid #0071ce;
        }

        .stTabs [role="tab"][aria-selected="true"] {
            border-bottom: 4px solid #ffc220;
            color: #0071ce;
        }

        .product-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            padding: 1em;
            border-radius: 6px;
            margin-bottom: 1em;
        }

        .cart-summary {
            font-weight: bold;
            color: #0071ce;
            padding-top: 0.5em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def product_card(name: str, price: float, description: str = "", rating: float = None):
    """Display a Walmart-style product card"""
    stars = f"{'⭐' * int(rating)}" if rating else ""
    st.markdown(
        f"""
        <div class="product-card">
            <strong>{name}</strong><br>
            <span style="color:#0071ce;">${price:.2f}</span><br>
            <small>{description}</small><br>
            <span style="color:#ffc220;">{stars}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def cart_summary(items: list):
    """Display a summary block with total and checkout button"""
    if not items:
        st.info("No items in cart.")
        return

    total = sum(item.get("price", 0) for item in items)
    st.markdown("---")
    st.subheader("Cart Summary")
    for item in items:
        st.markdown(f"- **{item['name']}** — ${item['price']:.2f}")
    st.markdown(f"<div class='cart-summary'>Total: ${total:.2f}</div>", unsafe_allow_html=True)

def walmart_navbar(title: str = "ReciPDF ➝ Walmart Cart"):
    st.markdown(
        f"""
        <div style="background:#0071ce;padding:0.75em 1em;color:white;font-weight:bold;border-radius:0 0 4px 4px;">
          {title}
        </div>
        """,
        unsafe_allow_html=True
    )
