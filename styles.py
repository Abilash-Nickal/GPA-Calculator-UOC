import streamlit as st

# --- DASHBOARD CSS STYLES (Light Theme Glassmorphism) ---
CSS_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Roboto:wght@400;500;700&display=swap');

    /* Remove underlines universally */
    a, a:hover, a:focus, a:active, a:visited, p, span, label { 
        text-decoration: none !important; 
        border-bottom: none !important; 
        outline: none !important; 
    }

    /* 1. Main Background and Typography */
    [data-testid="stAppViewContainer"] { 
        background: linear-gradient(135deg, #fff9f2 0%, #ffece0 50%, #fff3e8 100%) !important; 
        color: #1a1c29 !important; 
        font-family: 'Roboto', sans-serif; 
    }
    [data-testid="stHeader"] { 
        background: transparent !important; 
        color: #d96c34 !important;
    }
    [data-testid="stHeader"] button {
        color: #d96c34 !important;
    }
    [data-testid="block-container"] { padding-top: 2rem; }

    /* 2. Sidebar Aesthetics (Frosted Light) */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] { 
        background-color: rgba(255, 249, 242, 0.6) !important; 
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(235, 128, 68, 0.1) !important; 
    }
    
    /* Hide the radio widget's main label ("Navigation") */
    [data-testid="stSidebar"] div[data-testid="stWidgetLabel"] { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none !important; }

    /* 3. Dashboard Title and Headers */
    .top-header { display: flex; align-items: center; margin-bottom: 10px; gap: 10px; }
    .logo-circle { display: none; }
    .logo-text { font-family: 'Oswald', sans-serif; font-size: 1.5rem; letter-spacing: 2px; color: #1a1c29; }
    .dashboard-title { font-family: 'Oswald', sans-serif; font-size: 2rem !important; font-weight: 700 !important; color: #1a1c29 !important; margin-top: 5px; margin-bottom: 0 !important; text-transform: uppercase; }
    .dashboard-subtitle { color: #d96c34 !important; font-size: 0.85rem !important; font-weight: 600; text-transform: uppercase; margin-bottom: 2rem !important; letter-spacing: 1px; }

    /* 4. Custom Metric Cards (Glassmorphism + Floating Badge) */
    .ui-card { 
        background-color: rgba(253, 250, 247, 0.9); 
        backdrop-filter: blur(10px);
        border-radius: 2rem; 
        padding: 20px;
        box-shadow: 0 8px 30px rgba(235, 128, 68, 0.1); 
        border: 1px solid rgba(255, 255, 255, 0.9);
        margin-bottom: 1.5rem; 
        position: relative;
        transition: transform 0.3s ease;
    }
    .ui-card:hover { transform: translateY(-4px); }
    
    .ui-card-header { 
        position: absolute;
        top: -12px;
        right: 24px;
        background-color: #fbe7dc; 
        color: #d96c34; 
        font-family: 'Oswald', sans-serif; 
        font-size: 0.75rem; 
        letter-spacing: 1.5px; 
        padding: 4px 16px; 
        border-radius: 999px;
        border: 1px solid white;
        text-transform: uppercase; 
        box-shadow: 0 4px 15px rgba(235, 128, 68, 0.1);
        font-weight: 700;
        z-index: 10;
    }
    .ui-icon-block {
        background-color: #fbe7dc;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #d96c34;
        box-shadow: 0 4px 10px rgba(235,128,68,0.1);
    }
    .ui-icon-block svg { width: 24px; height: 24px; stroke: currentColor; }
    .ui-card-body { padding-top: 15px; display: flex; justify-content: space-between; align-items: center; }
    .ui-card-value { font-size: 2.2rem; font-weight: 700; color: #1a1c29; }
    .ui-card-subtext { font-size: 0.75rem; color: #d96c34; font-weight: 600; margin-top: 10px; font-family: monospace; letter-spacing: 0.1em; text-transform: uppercase; }
    .ui-icon-circle { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 10px rgba(235,128,68,0.2); }

    /* Style Buttons */
    .stButton > button {
        background-color: #fbe7dc !important;
        color: #d96c34 !important;
        border: 1px solid white !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-family: 'Oswald', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        height: auto !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #d96c34 !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(235,128,68,0.2) !important;
    }

    /* Style Tables */
    [data-testid="stDataFrame"] {
        background-color: rgba(253, 250, 247, 0.9) !important;
        border-radius: 1rem !important;
        padding: 10px !important;
    }

    /* Target Class Indicators */
    .class-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-family: 'Oswald', sans-serif;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .class-first { background-color: #ffead1; color: #d96c34; border: 1px solid #d96c34; }
    .class-second-upper { background-color: #e2f4ff; color: #3498db; border: 1px solid #3498db; }
    .class-second-lower { background-color: #e2fce6; color: #27ae60; border: 1px solid #27ae60; }
    .class-pass { background-color: #f5f5f5; color: #7f8c8d; border: 1px solid #7f8c8d; }

    /* Sidebar Navigation Premium Icons */
    div[role="radiogroup"] label {
        padding: 12px 15px !important;
        border-radius: 15px !important;
        margin-bottom: 5px !important;
        border: 1px solid transparent !important;
        transition: all 0.3s ease !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: rgba(217, 108, 52, 0.05) !important;
    }
    div[role="radiogroup"] label:has(input:checked) {
        background-color: #fbe7dc !important;
        border-left: 4px solid #d96c34 !important;
        box-shadow: 2px 4px 10px rgba(235,128,68,0.1) !important;
    }
    div[role="radiogroup"] label:has(input:checked) p { color: #d96c34 !important; font-weight: 700 !important; }
    
    div[role="radiogroup"] label p::before {
        content: ''; display: inline-block; width: 22px; height: 22px; margin-right: 15px; 
        background-size: contain; background-repeat: no-repeat; background-position: center;
        vertical-align: middle;
    }
    
    /* ICON 1: HOME */
    div[role="radiogroup"] > div:nth-child(1) label p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z' fill='%238c8f9c'/%3E%3C/svg%3E"); 
    }
    div[role="radiogroup"] > div:nth-child(1) label:has(input:checked) p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z' fill='%23d96c34'/%3E%3C/svg%3E"); 
    }
    
    /* ICON 2: MASTER DATA */
    div[role="radiogroup"] > div:nth-child(2) label p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M4 7h16v2H4V7zm0 4h16v2H4v-2zm0 4h16v2H4v-2zM4 3h16v2H4V3z' fill='%238c8f9c'/%3E%3C/svg%3E"); 
    }
    div[role="radiogroup"] > div:nth-child(2) label:has(input:checked) p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M4 7h16v2H4V7zm0 4h16v2H4v-2zm0 4h16v2H4v-2zM4 3h16v2H4V3z' fill='%23d96c34'/%3E%3C/svg%3E"); 
    }
    
    /* ICON 3: SEMESTER OVERVIEW */
    div[role="radiogroup"] > div:nth-child(3) label p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z' fill='%238c8f9c'/%3E%3C/svg%3E"); 
    }
    div[role="radiogroup"] > div:nth-child(3) label:has(input:checked) p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z' fill='%23d96c34'/%3E%3C/svg%3E"); 
    }
    
    /* ICON 4: INPUT RESULTS */
    div[role="radiogroup"] > div:nth-child(4) label p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z' fill='%238c8f9c'/%3E%3C/svg%3E"); 
    }
    div[role="radiogroup"] > div:nth-child(4) label:has(input:checked) p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z' fill='%23d96c34'/%3E%3C/svg%3E"); 
    }
    
    /* ICON 5: TARGET TRACKER */
    div[role="radiogroup"] > div:nth-child(5) label p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-12.5c-2.48 0-4.5 2.02-4.5 4.5s2.02 4.5 4.5 4.5 4.5-2.02 4.5-4.5-2.02-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%238c8f9c'/%3E%3C/svg%3E"); 
    }
    div[role="radiogroup"] > div:nth-child(5) label:has(input:checked) p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-12.5c-2.48 0-4.5 2.02-4.5 4.5s2.02 4.5 4.5 4.5 4.5-2.02 4.5-4.5-2.02-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z' fill='%23d96c34'/%3E%3C/svg%3E"); 
    }

    /* ICON 6: HELP & GUIDE */
    div[role="radiogroup"] > div:nth-child(6) label p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z' fill='%238c8f9c'/%3E%3C/svg%3E"); 
    }
    div[role="radiogroup"] > div:nth-child(6) label:has(input:checked) p::before { 
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z' fill='%23d96c34'/%3E%3C/svg%3E"); 
    }
    
    .social-footer { 
        display: flex; 
        flex-direction: row; 
        justify-content: center;
        gap: 20px; 
        padding-top: 30px;
        padding-bottom: 20px;
        margin-top: 40px;
        border-top: 1px solid rgba(235, 128, 68, 0.1);
    }
    .social-footer a { color: #8c8f9c !important; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; }
    .social-footer a:hover { color: #d96c34 !important; transform: translateY(-2px); }
    .social-footer svg { width: 24px; height: 24px; fill: currentColor; }
    
    /* Academic Button Target (Glassmorphism update) */
    div[data-testid="stElementContainer"]:has(.academic-btn-target) + div[data-testid="stElementContainer"] button {
        background-color: rgba(253, 250, 247, 0.9) !important; 
        backdrop-filter: blur(10px) !important;
        color: #1a1c29 !important; 
        height: 140px !important; 
        border-radius: 2.5rem !important; 
        border: 1px solid rgba(255, 255, 255, 0.9) !important; 
        box-shadow: 0 8px 30px rgba(235, 128, 68, 0.1) !important; 
        transition: transform 0.2s !important; 
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    div[data-testid="stElementContainer"]:has(.academic-btn-target) + div[data-testid="stElementContainer"] button:hover { 
        transform: translateY(-4px) !important; 
        box-shadow: 0 12px 35px rgba(235, 128, 68, 0.15) !important; 
        border-color: #fbe7dc !important; 
    }
    div[data-testid="stElementContainer"]:has(.academic-btn-target) + div[data-testid="stElementContainer"] button p {
        font-family: 'Oswald', sans-serif !important; font-size: 1.2rem !important; letter-spacing: 1px !important; color: #1a1c29 !important; display: flex; flex-direction: column; align-items: center; gap: 15px;
    }
    div[data-testid="stElementContainer"]:has(.academic-btn-target) + div[data-testid="stElementContainer"] button p::before {
        content: '↓'; display: flex; align-items: center; justify-content: center; width: 45px; height: 45px; background-color: #fbe7dc; border: 1px solid white; border-radius: 50%; font-size: 1.3rem; color: #d96c34; font-weight: bold;
    }

    /* Target Tracker UI */
    .target-card {
        background: linear-gradient(135deg, rgba(217, 108, 52, 0.05) 0%, rgba(217, 108, 52, 0.1) 100%);
        border: 1px dashed #d96c34;
        border-radius: 2rem;
        padding: 25px;
        margin-top: 15px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(235, 128, 68, 0.1); 
    }
    .target-value {
        font-family: 'Oswald', sans-serif;
        font-size: 2.5rem;
        color: #d96c34;
        margin: 10px 0;
    }
    .target-label {
        font-size: 0.85rem;
        color: #1a1c29;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .uni-logo {
        width: 100px;
        margin-bottom: 20px;
        filter: drop-shadow(0 4px 8px rgba(235,128,68,0.1));
    }
</style>
"""

# --- SVG ICONS FOR METRICS ---
ICON_CGPA = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><polyline points="3 17 9 11 13 15 21 7"></polyline></svg>'
ICON_CREDITS = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
ICON_SUBJECTS = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M4 9h4v11H4zm6-5h4v16h-4zm6 6h4v10h-4z"/></svg>'
ICON_PERFORMANCE = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg>'
ICON_EDIT = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>'
ICON_CALENDAR = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
ICON_TARGET = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'
ICON_HELP = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'

def apply_styles():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)

def render_custom_metric(title, value, subtext, icon, color):
    html = f"""
    <div class="ui-card">
        <div class="ui-card-header">{title}</div>
        <div class="ui-card-body">
            <div class="ui-card-value">{value}</div>
            <div class="ui-icon-block">{icon}</div>
        </div>
        <div class="ui-card-subtext">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
