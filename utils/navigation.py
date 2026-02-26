"""
Centralized navigation helpers for the Streamlit app.
Provides a reusable back-to-dashboard button used by all feature pages.
"""

import streamlit as st


def render_back_to_dashboard():
    """
    Render a '⬅ Back to Dashboard' button at the top of a feature page.
    Uses session state to navigate without full app reload.
    """
    if st.button("⬅ Back to Dashboard", key=f"back_dash_{st.session_state.get('dashboard_page', '')}"):
        st.session_state["dashboard_page"] = "dashboard_home"
        st.rerun()
    # Small visual spacer after the button
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
