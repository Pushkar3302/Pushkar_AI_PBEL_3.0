"""
Streamlit Theme & UI Components.
Supports Dynamic Light Mode / Dark Mode switching and header banners.
"""

import streamlit as st


def apply_custom_styles(theme: str = "Dark"):
    """Inject Theme CSS styles based on Light / Dark mode choice."""
    if theme == "Light":
        css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #F1F5F9 !important;
            border-right: 1px solid #CBD5E1 !important;
        }

        .header-banner {
            background: linear-gradient(90deg, #1D4ED8 0%, #3B82F6 100%);
            padding: 20px 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.15);
        }

        .header-title {
            font-size: 24px;
            font-weight: 700;
            color: #FFFFFF !important;
            margin: 0;
        }

        .header-subtitle {
            font-size: 13px;
            color: #E0F2FE !important;
            margin-top: 4px;
        }
        </style>
        """
    else:
        css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
            color: #F8FAFC !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        .header-banner {
            background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
            padding: 20px 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }

        .header-title {
            font-size: 24px;
            font-weight: 700;
            color: #FFFFFF !important;
            margin: 0;
        }

        .header-subtitle {
            font-size: 13px;
            color: #93C5FD !important;
            margin-top: 4px;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def render_header(title: str, subtitle: str):
    """Render header banner component."""
    html = f"""
    <div class="header-banner">
        <div class="header-title">🎓 {title}</div>
        <div class="header-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = "", delta_color: str = "#34D399"):
    """Render standard Streamlit metric component."""
    st.metric(label=label, value=value, delta=delta if delta else None)
