# src/styles.py

STYLE_CSS = """
<style>
/* Font overrides and import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"], [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
}

/* App background and root containers */
.main {
    background-color: #FAF9F6;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #F0EFEB !important;
    border-right: 1px solid #E5E5E0;
}

/* Sidebar Title and Info block */
.sidebar-title {
    font-size: 1.05rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4A5568;
    margin-bottom: 2rem;
    border-bottom: 1px solid #E5E5E0;
    padding-bottom: 0.75rem;
}

.sidebar-section {
    margin-bottom: 2rem;
}

.sidebar-footer {
    font-size: 0.75rem;
    color: #8A9A86;
    margin-top: 10rem;
    line-height: 1.5;
    border-top: 1px solid #E5E5E0;
    padding-top: 1rem;
}

/* Headers */
.main-title {
    font-size: 2.2rem;
    font-weight: 300;
    letter-spacing: -0.02em;
    color: #2D3748;
    margin-bottom: 0.25rem;
}

.main-subtitle {
    font-size: 0.95rem;
    font-weight: 400;
    color: #718096;
    margin-bottom: 2.5rem;
}

.section-header {
    font-size: 1.15rem;
    font-weight: 400;
    color: #4A5568;
    border-bottom: 1px solid #E5E5E0;
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
    letter-spacing: 0.02em;
}

/* Clean Custom Card for outputs */
.luxury-card {
    background-color: #FAF9F6;
    border: 1px solid #E5E5E0;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.01);
}

.luxury-card-title {
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #718096;
    margin-bottom: 0.75rem;
}

.prediction-pass {
    font-size: 2rem;
    font-weight: 300;
    color: #556B2F; /* Muted Olive Green */
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.prediction-fail {
    font-size: 2rem;
    font-weight: 300;
    color: #A27B75; /* Muted Rose/Terracotta */
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.probability-bar-container {
    margin-top: 1.25rem;
}

.probability-label {
    font-size: 0.85rem;
    color: #4A5568;
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.35rem;
}

/* Custom Styled Buttons */
div.stButton > button {
    background-color: #FAF9F6 !important;
    color: #4A5568 !important;
    border: 1px solid #D1D1CB !important;
    border-radius: 4px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 400 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.25s ease !important;
    box-shadow: none !important;
}

div.stButton > button:hover {
    background-color: #F0EFEB !important;
    border-color: #9A9A90 !important;
    color: #2D3748 !important;
}

div.stButton > button:focus {
    box-shadow: 0 0 0 1px #9A9A90 !important;
    outline: none !important;
}

/* Sliders custom styles to fit aesthetics */
div[data-baseweb="slider"] {
    margin-bottom: 1.5rem;
}

/* Adjust layout containers */
div.block-container {
    padding-top: 4rem !important;
    padding-bottom: 4rem !important;
    max-width: 900px !important;
}

/* Custom cards for historical log display */
.log-card {
    background-color: #FAF9F6;
    border: 1px solid #E5E5E0;
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}
</style>
"""

def inject_styles():
    import streamlit as st
    st.markdown(STYLE_CSS, unsafe_allow_html=True)
