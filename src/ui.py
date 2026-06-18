from __future__ import annotations

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {padding-top: 1.5rem; max-width: 1280px;}
        .metric-card {background:#fff;border-radius:18px;padding:18px;border:1px solid #e8ecf3;box-shadow:0 6px 18px rgba(10,20,40,.05)}
        .hero {background:linear-gradient(135deg,#123328,#0f7b5c);color:white;padding:28px;border-radius:24px;margin-bottom:18px;}
        .hero h1 {margin:0;font-size:2.2rem;}
        .badge {padding:4px 10px;border-radius:999px;background:#e7f6ef;color:#0f7b5c;font-weight:700;font-size:.78rem;}
        .secret-card {border:1px solid #e7eaf0;border-radius:18px;padding:18px;background:#fff;margin-bottom:12px;}
        .stButton>button {border-radius:12px;font-weight:700;}
        div[data-testid="stSidebar"] {background:#10251f;color:white;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(f"""<div class='hero'><span class='badge'>Secret Star Restaurant</span><h1>{title}</h1><p>{subtitle}</p></div>""", unsafe_allow_html=True)


def require_login() -> bool:
    if "user" not in st.session_state:
        st.warning("Effettua il login per accedere alla piattaforma.")
        return False
    return True
