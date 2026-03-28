import streamlit as st
import pandas as pd
import plotly.express as px
import styles
from styles import ICON_CGPA, ICON_CREDITS, ICON_SUBJECTS, ICON_PERFORMANCE, ICON_EDIT, ICON_CALENDAR, ICON_TARGET, ICON_HELP, render_custom_metric, render_notice
from logic import parse_pasted_data, process_combined_data, get_classification, calculate_target_required_gpa, universal_save, universal_load

# --- Page Configuration ---
st.set_page_config(
    page_title="UOC FOT GPA Calculator | University of Colombo Faculty of Technology",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://abilash-portfolio-5601e.web.app/',
        'Report a bug': "https://github.com/Abilash-Nickal/GPA-Calculator-UOC/issues",
        'About': """
            # UOC FOT GPA Calculator
            Built for students of the **Faculty of Technology, University of Colombo**.
            Supports BET, BICT, and BBST degree programs.
            Developed by Abilash.
        """
    }
)

# --- PERSISTENT DATA STORAGE (per-user session, NOT shared across users) ---
if "df" not in st.session_state:
    st.session_state.df = None

# --- APPLY CUSTOM STYLES ---
styles.apply_styles()

# Hidden SEO Block - This helps Google index your app for specific UOC keywords
st.markdown("""
    <div style="display:none;">
        <h1>GPA Calculator for University of Colombo (UOC)</h1>
        <h2>Faculty of Technology (FOT) - Pitipana Campus</h2>
        <p>
            Official-style GPA and CGPA calculator for University of Colombo Technology students. 
            Compatible with:
            - Bachelor of Engineering Technology (BET)
            - Bachelor of Information and Communication Technology (BICT)
            - Bachelor of Biosystems Technology (BBST)
            - Instrumentation and Automation, Agriculture, and Environmental Technology.
        </p>
        <p>Keywords: UOC GPA, FOT GPA, University of Colombo GPA Calculator, 
           Abilash GPA, Semester GPA UOC, Colombo University Technology Faculty.</p>
    </div>
""", unsafe_allow_html=True)
# --- Navigation Setup ---
options = ["HOME", "EDIT MASTER DATA", "SEMESTER OVERVIEW", "INPUT RESULTS", "TARGET TRACKER", "HELP & GUIDE", "FEEDBACK"]
if "nav_index" not in st.session_state:
    st.session_state.nav_index = 0
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "target_class" not in st.session_state:
    st.session_state.target_class = "2ND UPPER (3.30)"
if "total_deg_credits" not in st.session_state:
    st.session_state.total_deg_credits = 120.0

with st.sidebar:
    st.markdown(f"""
    <div style="display:flex; flex-direction:column; align-items:center; margin-bottom: 10px; margin-top: 0px;">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/f/f9/Logo_of_the_University_of_Colombo.png/250px-Logo_of_the_University_of_Colombo.png" class="uni-logo">
        <h1 style="color:#d96c34; font-family:'Oswald', sans-serif; letter-spacing: 2px; margin:0; font-size:1.4rem; text-align:center; text-transform:uppercase;">
        Academic Tracker
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # NATIVE ZERO-BLINK RADIO NAVIGATION
    # Remove key to allow programmatic index updates without API Exceptions
    current_page = st.radio("Navigation", options, index=st.session_state.nav_index, label_visibility="collapsed")
    
    # Sync index back for buttons
    st.session_state.nav_index = options.index(current_page)
    

    
    # Auth Logic
    st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        
    if not st.session_state.authenticated:
        st.caption("Status: **Guest Mode** (Local Save)")
        if st.button("Login / Create Account", icon=":material/login:", type="primary", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
        if st.button("Save Locally (Guest)", icon=":material/save:", use_container_width=True):
            if st.session_state.df is not None:
                success, msg = universal_save(st.session_state.df, user_id=None)
                if success:
                    st.success("Saved to your browser.")
                    st.caption("💡 Login to sync across devices.")
                else:
                    st.error(msg)
            else:
                st.warning("No data to save yet!")
    else:
        st.caption(f"Status: **Logged in** ({st.session_state.user_id})")
        if st.button("Save Progress", icon=":material/save:", type="primary", use_container_width=True):
            if st.session_state.df is not None:
                success, msg = universal_save(st.session_state.df, user_id=st.session_state.user_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("No data to save yet!")
        if st.button("Logout", icon=":material/logout:", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.df = None
            st.rerun()

    # Bottom Social & Link Footer
    st.markdown(f"""
    <div class="social-footer">
        <a href="https://www.linkedin.com/in/arumugam-abilashan-6916a2157" target="_blank" title="LinkedIn">
            <svg viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
        </a>
        <a href="https://github.com/Abilash-Nickal" target="_blank" title="GitHub">
            <svg viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </a>
        <a href="https://abilash-portfolio-5601e.web.app/" target="_blank" title="Web Portal">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </a>
        <a href="https://sis.cmb.ac.lk/tech/results/result_sheet" target="_blank" title="SIS Link"> 
            <svg viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>
        </a>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# DATA PREPARATION
# ==========================================
# Auto-load only for logged-in users (guests start with zero data by design)
# This runs once per session when df has not been loaded yet
if st.session_state.df is None and st.session_state.get("authenticated"):
    uid = st.session_state.get("user_id")
    init_df, load_msg = universal_load(user_id=uid)
    if init_df is not None and not init_df.empty:
        st.session_state.df = init_df

df = st.session_state.df
included_df = pd.DataFrame()
total_credits, final_gpa, performance_pct = 0, 0.0, 0.0

if df is not None:
    df['credits'] = pd.to_numeric(df['credits'], errors='coerce').fillna(0)
    df['gpv'] = pd.to_numeric(df['gpv'], errors='coerce').fillna(0)
    included_df = df[df['Include'] == True]
    
    total_credits = included_df['credits'].sum()
    total_gp = (included_df['credits'] * included_df['gpv']).sum()
    final_gpa = total_gp / total_credits if total_credits > 0 else 0.0
    performance_pct = (final_gpa / 4.0) * 100


# ==========================================
# PAGE CONTENT RENDERING
# ==========================================

# RENDER LOGIN UI IF REQUESTED (AS AN OVERLAY)
if st.session_state.show_login and not st.session_state.authenticated:
    st.markdown("""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">CLOUD SYNC & LOGIN</h1>
    <p class="dashboard-subtitle">Home > Login</p>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="ui-card-header" style="top:-15px;">AUTHENTICATION</div>', unsafe_allow_html=True)
        
        st.info("Guest Mode Active. Your data is currently saving to the local browser. Login to sync with the cloud.")
        cloud_user = st.text_input("Enter Student ID to Login")
        
        login_col1, login_col2 = st.columns(2)
        with login_col1:
            if st.button("Login to Cloud", icon=":material/login:", type="primary", use_container_width=True):
                if cloud_user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = cloud_user
                    st.session_state.show_login = False
                    # Always reset data on login and load fresh from cloud
                    st.session_state.df = None
                    cloud_df, msg = universal_load(user_id=cloud_user)
                    if cloud_df is not None and not cloud_df.empty:
                        st.session_state.df = cloud_df
                    st.rerun()
                else:
                    st.error("Please enter a valid Student ID.")
        with login_col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # Prevents rendering of any other page content while login is active

# Ensure show_login is False if already authenticated
if st.session_state.authenticated:
    st.session_state.show_login = False

# --------- PAGE: HOME ---------
if current_page == "HOME":
    standing = get_classification(final_gpa) if df is not None else "AWAITING DATA"
    st.markdown(f"""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
        <div style="margin-left: auto; background:#fbe7dc; color:#d96c34; padding:5px 15px; border-radius:15px; font-family:'Oswald',sans-serif; font-size:0.9rem; border:1px solid #d96c34;">
            {standing}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown('<h1 class="dashboard-title" style="margin-bottom:0px !important;">HOME</h1>', unsafe_allow_html=True)
        st.markdown('<p class="dashboard-subtitle">Home > Tracker</p>', unsafe_allow_html=True)
    with col_h2:
        st.write("###") # Vertical spacer
        if st.button("+ INPUT NEW RESULTS", type="primary", use_container_width=True, icon=":material/add_circle:"):
            st.session_state.nav_index = options.index("INPUT RESULTS")
            st.rerun()

    # --- AUTO-SAVE DEFERRED FROM INPUT PAGE ---
    if st.session_state.get("pending_save"):
        uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None
        success, msg = universal_save(st.session_state.df, user_id=uid)
        if success: st.toast(f"✅ {msg}", icon="📦")
        else: st.error(msg)
        st.session_state.pending_save = False

    if df is None:
        render_notice("Please navigate to 'INPUT RESULTS' on the left or use the button above to load your academic data.", icon="help")
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_custom_metric("FINAL CGPA", "0.00", "+0.00 SINCE LAST SEMESTER", ICON_CGPA, "#2B2D38")
        with m2: render_custom_metric("TOTAL CREDITS", "0", "AWAITING DATA", ICON_CREDITS, "#87DE96")
        with m3: render_custom_metric("SUBJECTS PASSED", "0", "AWAITING DATA", ICON_SUBJECTS, "#FA8A76")
        with m4: render_custom_metric("PERFORMANCE", "0%", "AWAITING DATA", ICON_PERFORMANCE, "#2B2D38")
    else:
        # ROW 1: Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_custom_metric("FINAL CGPA", f"{final_gpa:.4f}", "+ ACTIVE SEMESTER", ICON_CGPA, "#d96c34")
        with m2: render_custom_metric("TOTAL CREDITS", f"{int(total_credits)}", "+ ACTIVE SEMESTER", ICON_CREDITS, "#d96c34")
        with m3: render_custom_metric("SUBJECTS PASSED", f"{len(included_df)}", "+ ACTIVE SEMESTER", ICON_SUBJECTS, "#d96c34")
        with m4: render_custom_metric("PERFORMANCE", f"{performance_pct:.1f}%", "+ ACTIVE SEMESTER", ICON_PERFORMANCE, "#d96c34")

        # --- DEGREE TARGET SNAPSHOT ROW ---
        st.write("")
        # Read user's target from session state (set in Target Tracker), with sensible defaults
        target_map = {"FIRST CLASS (3.70)": 3.70, "2ND UPPER (3.30)": 3.30, "2ND LOWER (3.00)": 3.00}
        target_cls_label = st.session_state.get("target_class", "2ND UPPER (3.30)")
        target_gpa_threshold = target_map[target_cls_label]
        target_cls_name = target_cls_label.split(" (")[0]  # e.g. "2ND UPPER"
        DEFAULT_TOTAL_CREDITS = st.session_state.get("total_deg_credits", 120.0)
        cls_colors = {"FIRST CLASS": "#d4a017", "2ND UPPER": "#a8a8a8", "2ND LOWER": "#cd7f32", "GENERAL": "#8c8f9c"}

        needed = calculate_target_required_gpa(target_gpa_threshold, final_gpa, total_credits, DEFAULT_TOTAL_CREDITS)
        target_color = cls_colors.get(target_cls_name, "#8c8f9c")

        t1, t2, t3, t4 = st.columns(4)
        with t1:
            badge_color = cls_colors.get(standing, "#8c8f9c")
            st.markdown(f"""
            <div style="background:rgba(253,250,247,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.8);
                        border-radius:1rem; padding:16px 20px; text-align:center;">
                <div style="font-size:0.7rem; color:#8c8f9c; font-family:'Oswald',sans-serif; letter-spacing:1.5px; margin-bottom:6px;">CURRENT STANDING</div>
                <div style="font-size:1.1rem; font-weight:800; color:{badge_color}; font-family:'Oswald',sans-serif;">{standing}</div>
            </div>
            """, unsafe_allow_html=True)
        with t2:
            if needed is not None and 0 <= needed <= 4.0:
                st.markdown(f"""
                <div style="background:rgba(253,250,247,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.8);
                            border-radius:1rem; padding:16px 20px; text-align:center;">
                    <div style="font-size:0.7rem; color:#8c8f9c; font-family:'Oswald',sans-serif; letter-spacing:1.5px; margin-bottom:6px;">TARGET: {target_cls_name}</div>
                    <div style="font-size:1.1rem; font-weight:800; color:{target_color}; font-family:'Oswald',sans-serif;">{needed:.2f} avg needed</div>
                </div>
                """, unsafe_allow_html=True)
            elif needed is not None and needed < 0:
                st.markdown(f"""
                <div style="background:rgba(253,250,247,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.8);
                            border-radius:1rem; padding:16px 20px; text-align:center;">
                    <div style="font-size:0.7rem; color:#8c8f9c; font-family:'Oswald',sans-serif; letter-spacing:1.5px; margin-bottom:6px;">TARGET: {target_cls_name}</div>
                    <div style="font-size:1.1rem; font-weight:800; color:#27ae60; font-family:'Oswald',sans-serif;">Already reached! 🎉</div>
                </div>
                """, unsafe_allow_html=True)
            elif needed is not None and needed > 4.0:
                st.markdown(f"""
                <div style="background:rgba(253,250,247,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.8);
                            border-radius:1rem; padding:16px 20px; text-align:center;">
                    <div style="font-size:0.7rem; color:#8c8f9c; font-family:'Oswald',sans-serif; letter-spacing:1.5px; margin-bottom:6px;">TARGET: {target_cls_name}</div>
                    <div style="font-size:1.1rem; font-weight:800; color:#e74c3c; font-family:'Oswald',sans-serif;">Not Achievable</div>
                </div>
                """, unsafe_allow_html=True)
        with t3:
            remaining = DEFAULT_TOTAL_CREDITS - total_credits
            pct_done = min((total_credits / DEFAULT_TOTAL_CREDITS) * 100, 100)
            st.markdown(f"""
            <div style="background:rgba(253,250,247,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.8);
                        border-radius:1rem; padding:16px 20px; text-align:center;">
                <div style="font-size:0.7rem; color:#8c8f9c; font-family:'Oswald',sans-serif; letter-spacing:1.5px; margin-bottom:6px;">DEGREE PROGRESS</div>
                <div style="font-size:1.1rem; font-weight:800; color:#d96c34; font-family:'Oswald',sans-serif;">{pct_done:.1f}% done</div>
                <div style="margin-top:6px; background:#fbe7dc; border-radius:10px; height:6px;">
                    <div style="background:#d96c34; border-radius:10px; height:6px; width:{pct_done:.1f}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with t4:
            remaining_cr = max(DEFAULT_TOTAL_CREDITS - total_credits, 0)
            st.markdown(f"""
            <div style="background:rgba(253,250,247,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.8);
                        border-radius:1rem; padding:16px 20px; text-align:center;">
                <div style="font-size:0.7rem; color:#8c8f9c; font-family:'Oswald',sans-serif; letter-spacing:1.5px; margin-bottom:6px;">CREDITS REMAINING</div>
                <div style="font-size:1.1rem; font-weight:800; color:#1a1c29; font-family:'Oswald',sans-serif;">{int(remaining_cr)} / {int(DEFAULT_TOTAL_CREDITS)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.write("")

        # Prepare Graph Data
        sem_stats = []
        semesters = included_df.groupby(['academic_level', 'semester'])
        for (lvl, sem), group in semesters:
            s_cred = group['credits'].sum()
            s_pts = (group['credits'] * group['gpv']).sum()
            sem_stats.append({
                "Term": f"L{lvl} - S{sem}", 
                "SGPA": s_pts / s_cred if s_cred > 0 else 0.0, 
                "Credits": s_cred, 
                "Subjects": len(group)
            })
        df_trends = pd.DataFrame(sem_stats)

        # ROW 2: Layout
        st.write("") 
        col_left, col_right = st.columns([1, 3])
        with col_left:
            st.markdown('<div class="ui-card"><div class="ui-card-header">GRADE DISTRIBUTION</div>', unsafe_allow_html=True)
            if not included_df.empty:
                # Prepare Pie Chart Data
                grade_counts = included_df['grade'].value_counts().reset_index()
                grade_counts.columns = ['Grade', 'Count']
                
                # Define a consistent peach-navy color scale
                color_map = {
                    'A': '#d96c34', 'A-': '#e2875b', 'B+': '#eba181', 'B': '#f3bcad',
                    'B-': '#fbe7dc', 'C+': '#8c8f9c', 'C': '#1a1c29', 'Other': '#d1d4db'
                }
                
                fig_p = px.pie(grade_counts, values='Count', names='Grade', hole=0.4, 
                               color='Grade', color_discrete_map=color_map)
                fig_p.update_traces(textposition='inside', textinfo='percent+label')
                fig_p.update_layout(
                    showlegend=False, 
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=5, r=5, t=5, b=5), height=230
                )
                st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="ui-card"><div class="ui-card-header">PERCENTAGE (SGPA TREND)</div><div style="padding: 10px;">', unsafe_allow_html=True)
            if not df_trends.empty:
                # Graph 1: SGPA Line chart showing exact point values and clear Y-axis
                fig_l = px.line(df_trends, x="Term", y="SGPA", markers=True, text="SGPA")
                fig_l.update_traces(
                    textposition="top center", texttemplate='%{text:.2f}',
                    line=dict(color='#d96c34', width=2), 
                    marker=dict(size=8, color='#d96c34', line=dict(color='white', width=2))
                )
                fig_l.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#8c8f9c'), margin=dict(l=10, r=20, t=25, b=10), height=250, 
                    xaxis=dict(showgrid=False, title="", showline=True, linecolor='#fbe7dc', tickfont=dict(color='#1a1c29')), 
                    yaxis=dict(visible=True, showgrid=True, gridcolor='#fbe7dc', range=[0, 4.3], title=dict(text="SGPA Score", font=dict(color='#1a1c29')), showticklabels=True, tickfont=dict(size=11, color='#1a1c29'))
                )
                st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div></div>', unsafe_allow_html=True)

        # ROW 3: Visual Insights
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="bar-chart-header">GRADE COUNTS OVERVIEW</div>', unsafe_allow_html=True)
            if not included_df.empty:
                st.markdown('<div style="background-color: rgba(253, 250, 247, 0.4); backdrop-filter: blur(10px); padding: 20px; border-radius: 0 0 2rem 2rem; border: 1px solid rgba(255, 255, 255, 0.8); border-top:none; box-shadow: 0 8px 30px rgba(235, 128, 68, 0.05); margin-bottom: 2rem;">', unsafe_allow_html=True)
                # Prepare Grade Counts
                gc = included_df['grade'].value_counts().reset_index()
                gc.columns = ['Grade', 'Count']
                gc = gc.sort_values('Grade')
                
                fig_gc = px.bar(gc, x='Grade', y='Count', text='Count', color_discrete_sequence=['#d96c34'])
                fig_gc.update_traces(textposition='outside')
                fig_gc.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#1a1c29', size=11), margin=dict(l=10, r=10, t=25, b=10), height=220, 
                    xaxis=dict(visible=True, showgrid=False, title="", tickfont=dict(color='#1a1c29')), 
                    yaxis=dict(visible=True, showgrid=True, gridcolor='rgba(217, 108, 52, 0.1)', title="Count", showticklabels=True, tickfont=dict(color='#1a1c29'))
                )
                st.plotly_chart(fig_gc, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="bar-chart-header">CREDITS & SUBJECTS PER SEMESTER</div>', unsafe_allow_html=True)
            if not df_trends.empty:
                st.markdown('<div style="background-color: rgba(253, 250, 247, 0.4); backdrop-filter: blur(10px); padding: 20px; border-radius: 0 0 2rem 2rem; border: 1px solid rgba(255, 255, 255, 0.8); border-top:none; box-shadow: 0 8px 30px rgba(235, 128, 68, 0.05); margin-bottom: 2rem;">', unsafe_allow_html=True)
                
                # Melt dataframe to compare Credits and Subjects side-by-side
                df_melted = df_trends.melt(id_vars="Term", value_vars=["Credits", "Subjects"], var_name="Metric", value_name="Value")
                
                fig_b = px.bar(df_melted, x="Term", y="Value", color="Metric", barmode='group', text="Value", color_discrete_sequence=['#1a1c29', '#d96c34'])
                fig_b.update_traces(textposition='outside', marker_line_width=0, opacity=1, textfont=dict(color='#1a1c29', size=11))
                fig_b.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#1a1c29', size=11), margin=dict(l=10, r=10, t=25, b=10), height=220, 
                    xaxis=dict(visible=True, showgrid=False, title="", tickfont=dict(color='#1a1c29')), 
                    yaxis=dict(visible=True, showgrid=True, gridcolor='rgba(217, 108, 52, 0.1)', title="Count", showticklabels=True, tickfont=dict(color='#1a1c29')),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
                )
                st.plotly_chart(fig_b, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
# --------- PAGE: TARGET TRACKER ---------
elif current_page == "TARGET TRACKER":
    st.markdown("""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">TARGET TRACKER</h1>
    <p class="dashboard-subtitle">Home > Target Tracker</p>
    """, unsafe_allow_html=True)

    if df is None:
        render_notice("No data available. Please navigate to 'INPUT RESULTS' first to use the tracker.", icon="help")
    else:
        st.write("---")
        st.markdown(f"""
        <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; margin-bottom:20px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
            <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_TARGET}</div>
            ACADEMIC TARGET TRACKER
        </h3>
        """, unsafe_allow_html=True)
        t_col1, t_col2 = st.columns([2, 1])
        
        with t_col1:
            st.write("Plan your path to your desired degree classification. Enter your target and total credits for the degree.")
            
            target_class = st.selectbox("SET TARGET CLASS",
                ["FIRST CLASS (3.70)", "2ND UPPER (3.30)", "2ND LOWER (3.00)"],
                index=["FIRST CLASS (3.70)", "2ND UPPER (3.30)", "2ND LOWER (3.00)"].index(st.session_state.target_class))
            
            if target_class != st.session_state.target_class:
                st.session_state.target_class = target_class
                uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None
                universal_save(st.session_state.df, user_id=uid)
                st.rerun()

            target_map = {"FIRST CLASS (3.70)": 3.70, "2ND UPPER (3.30)": 3.30, "2ND LOWER (3.00)": 3.00}
            target_gpa_val = target_map[target_class]
            
            total_deg_credits = st.number_input("TOTAL DEGREE CREDITS", min_value=1.0, value=st.session_state.total_deg_credits, step=1.0)
            if total_deg_credits != st.session_state.total_deg_credits:
                st.session_state.total_deg_credits = total_deg_credits
                uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None
                universal_save(st.session_state.df, user_id=uid)
                st.rerun()
            
        with t_col2:
            req_gpa = calculate_target_required_gpa(target_gpa_val, final_gpa, total_credits, total_deg_credits)
            
            if req_gpa is None:
                st.warning("Degree already completed or total credits invalid.")
            elif req_gpa > 4.0:
                st.error(f"Mathematically impossible to reach {target_class}. You need {req_gpa:.2f} avg.")
            elif req_gpa < 0:
                st.success(f"You have already reached the requirement for {target_class}!")
            else:
                st.markdown(f"""
                <div class="target-card">
                    <div class="target-label">Min Grade Required</div>
                    <div class="target-value">{req_gpa:.2f}</div>
                    <div class="target-label">Avg GPA per Subject</div>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"Based on {total_deg_credits - total_credits:.0f} remaining credits.")


# --------- PAGE: EDIT MASTER DATA ---------
elif current_page == "EDIT MASTER DATA":
    st.markdown("""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">EDIT MASTER DATA</h1>
    <p class="dashboard-subtitle">Home > Master Data</p>
    """, unsafe_allow_html=True)

    if df is None:
        render_notice("No data to edit. Please navigate to 'INPUT RESULTS' first.", icon="edit")
    else:
        st.markdown(f"""
        <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; margin-bottom:10px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
            <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_EDIT}</div>
            Manage & Edit Course Data
        </h3>
        """, unsafe_allow_html=True)
        st.caption("You can freely edit cells, check/uncheck courses, and instantly affect your dashboard metrics.")
        
        column_config = {
            "Include": st.column_config.CheckboxColumn("Include", default=True),
            "Order": st.column_config.NumberColumn("Order", min_value=1, step=1, help="Sort items by this value"),
            "academic_level": st.column_config.TextColumn("Lvl"), "semester": st.column_config.TextColumn("Sem"),
            "course_code": st.column_config.TextColumn("Code"), "course_title": st.column_config.TextColumn("Title"),
            "credits": st.column_config.NumberColumn("Crd"), "gpv": st.column_config.NumberColumn("GPV", min_value=0.0, max_value=4.0),
            "grade": st.column_config.TextColumn("Grade"),
            "Remarks": st.column_config.TextColumn("Remarks"),
        }
        display_cols = ['Order', 'Include', 'academic_level', 'semester', 'course_code', 'course_title', 'credits', 'gpv', 'grade', 'Remarks']
        
        # Ensure 'Order' and 'Remarks' exist in df if not already there
        if 'Order' not in df.columns:
            df['Order'] = range(1, len(df) + 1)
        if 'Remarks' not in df.columns:
            df['Remarks'] = ""

        edited_df = st.data_editor(
            df[display_cols].sort_values('Order'), 
            column_config=column_config, 
            use_container_width=True, 
            hide_index=True, 
            num_rows="dynamic", 
            key="main_editor"
        )
        
        if not edited_df.equals(df):
            st.session_state.df = edited_df
            uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None
            universal_save(edited_df, user_id=uid)
            st.rerun()

# --------- PAGE: SEMESTER OVERVIEW ---------
elif current_page == "SEMESTER OVERVIEW":
    st.markdown("""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">SEMESTER OVERVIEW</h1>
    <p class="dashboard-subtitle">Home > Overview</p>
    """, unsafe_allow_html=True)

    if df is None or included_df.empty:
        render_notice("No data available. Please input results first.", icon="help")
    else:
        # Group by level and then semester to create a clean grouped layout
        levels = sorted(included_df['academic_level'].unique())
        
        for level in levels:
            # 1. Level Header
            st.markdown(f"""
            <div style="margin-top: 30px; margin-bottom: 20px;">
                <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; margin:0; display: flex; align-items: center; gap: 12px; text-transform:uppercase;">
                    <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_CALENDAR}</div>
                    ACADEMIC LEVEL {level}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            level_df = included_df[included_df['academic_level'] == level]
            sem_groups = sorted(level_df['semester'].unique())
            num_sems = len(sem_groups)
            
            if num_sems > 0:
                # Dynamic columns perfectly fit the number of semesters (usually 2, splits screen 50/50)
                card_cols = st.columns(num_sems)
                
                # Row 1: The Summary Cards
                for idx, sem in enumerate(sem_groups):
                    group = level_df[level_df['semester'] == sem]
                    s_cred = group['credits'].sum()
                    s_points = (group['credits'] * group['gpv']).sum()
                    s_gpa = s_points / s_cred if s_cred > 0 else 0.0
                    
                    with card_cols[idx]:
                        st.markdown(f"""
                        <div class="ui-card">
                            <div class="ui-card-header">Sem {sem}</div>
                            <div class="ui-card-body">
                                <div class="ui-card-value" style="color:#d96c34;">{s_gpa:.4f}</div>
                            </div>
                            <div class="ui-card-subtext">CREDITS: {s_cred} &nbsp;·&nbsp; SUBJECTS: {len(group)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Row 2: The Course Tables (placed directly underneath their respective cards)
                table_cols = st.columns(num_sems)
                for idx, sem in enumerate(sem_groups):
                    group = level_df[level_df['semester'] == sem]
                    with table_cols[idx]:
                        display_group = group[['course_title', 'gpv']].copy()
                        display_group.columns = ['Course', 'GPV']
                        st.dataframe(display_group, hide_index=True, use_container_width=True)


# --------- PAGE: INPUT RESULTS ---------
elif current_page == "INPUT RESULTS":
    st.markdown("""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">INPUT RESULTS</h1>
    <p class="dashboard-subtitle">Home > Data Entry</p>
    """, unsafe_allow_html=True)

    st.markdown("### Paste all your results from the university web portal:")
    raw_paste = st.text_area("Paste results here (you can paste multiple levels or semesters at once)", height=300, placeholder="Example:\nIA 1201  Pre-Calculus... \nIA 1202  Electricity...")

    st.write("---")
    
    if st.button("🚀 PROCESS DATA & VIEW DASHBOARD", type="primary", use_container_width=True):
        if not raw_paste.strip():
            st.error("Paste your data into the box first!")
        else:
            new_parsed_data = parse_pasted_data(raw_paste)
            
            if not new_parsed_data:
                st.error("No valid course data found in the pasted text. Please check the format.")
            else:
                # CONTINUOUS ADDING LOGIC: Combine new results with existing ones
                total_data = []
                if st.session_state.df is not None:
                    # Convert existing DataFrame back to raw record format for re-processing
                    # We drop calculated columns that process_combined_data will recreate
                    existing_raw = st.session_state.df.to_dict('records')
                    total_data.extend(existing_raw)
                
                total_data.extend(new_parsed_data)
                
                df_final, error = process_combined_data(total_data)
                if error: st.error(error)
                else:
                    st.session_state.df = df_final
                    st.session_state.nav_index = options.index("HOME")
                    # Defer save to the home page for immediate navigation
                    st.session_state.pending_save = True
                    st.rerun()
# --------- PAGE: LOGIN / SYNC ---------
# --------- PAGE: HELP & GUIDE ---------
elif current_page == "HELP & GUIDE":
    st.markdown("""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">HELP & GUIDE</h1>
    <p class="dashboard-subtitle">Home > Help & Guide</p>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">:material/play_circle:</div>
        Demo Video (How to Use)
    </h3>
    """, unsafe_allow_html=True)
    st.video("https://youtu.be/kfrPbWMncnc")
    
    st.write("---")

    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_HELP}</div>
        Data Import Guide
    </h3>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    1. Open your **Result Sheet** in the student portal.
    2. **Select & Copy** the entire results table.
    3. Navigate to **INPUT RESULTS** in this app.
    4. **Paste** the copied text and click **PROCESS DATA**.
    """)
    st.image("image.png", caption="1. Copy your results from the University Portal", use_container_width=True)
    st.image("image copy.png", caption="2. Paste into the Input Results section", use_container_width=True)

    st.write("---")
    
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_CGPA}</div>
        Data Storage & Cloud Sync
    </h3>
    """, unsafe_allow_html=True)
    st.markdown("""
    **Never Lose Your Progress!**
    - **Guest Mode (Local Save):** By default, clicking **Save Progress** securely stores your data right inside your web browser.
    - **Create an Account (Cloud Sync):** Go to the **LOGIN / SYNC** page and enter your Student ID (this automatically creates your account!). Once logged in, your tracker data is securely synced to the cloud so you can access it from your phone, laptop, or any other device.
    """)

    st.write("---")
    
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_TARGET}</div>
        Strategic Planning (Target Tracker)
    </h3>
    """, unsafe_allow_html=True)
    st.markdown("Use the **Target Tracker** to calculate exactly what GPA you need in your remaining subjects to reach your goal.")
    st.image("image copy 2.png", caption="Strategic Planning in Target Tracker", use_container_width=True)

    st.write("---")
    
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_EDIT}</div>
        Manage Your Data (Master Data)
    </h3>
    """, unsafe_allow_html=True)
    st.markdown("In **Master Data**, you can manually adjust results, add remarks, and reorder subjects for a perfect dashboard view.")
    st.image("image copy 3.png", caption="Managing and reordering in Master Data", use_container_width=True)

    st.write("---")
    
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">:material/install_mobile:</div>
        Install as a Mobile App (PWA)
    </h3>
    """, unsafe_allow_html=True)
    
    col_pwa1, col_pwa2 = st.columns(2)
    with col_pwa1:
        st.markdown("""
        **🍎 For iPhone (Safari)**
        1. Open Safari and go to your tracker URL.
        2. Tap the **Share** button (square with arrow up).
        3. Scroll and tap **"Add to Home Screen"**.
        4. Tap **"Add"** in the top right.
        """)
    with col_pwa2:
        st.markdown("""
        **🤖 For Android (Chrome)**
        1. Open Chrome and go to your tracker URL.
        2. Tap the **Menu** (three dots ⋮).
        3. Tap **"Add to Home screen"** or **"Install App"**.
        4. Tap **"Add"** to confirm.
        """)
    
    st.info("Once installed, the Academic Tracker will appear on your home screen and open in full-screen mode like a native app!")

    st.write("---")
    st.markdown("### Core Features Overview")
    st.markdown("""
    - **Cloud Sync & Local Backup**: Save data locally or sync across devices by logging in.\n    - **Dashboard Overview**: Real-time CGPA and SGPA trend analysis.\n    - **Master Data**: Edit, reorder, and add remarks to your course results.\n    - **Semester Overview**: Level-by-level performance breakdown.\n    - **Target Tracker**: Plan your path to success.\n    - **Data Import**: Intelligent parsing from university portal results.
    """ )

    st.write("---")
    st.caption("UOC Academic Tracker • v2.0 • Created by Abilash")

# --------- PAGE: FEEDBACK ---------
if current_page == "FEEDBACK":
    st.markdown(f"""
    <div class="top-header">
        <div class="logo-text">ACADEMIC TRACKER</div>
    </div>
    <h1 class="dashboard-title">SHARE FEEDBACK</h1>
    <p class="dashboard-subtitle">Home > Feedback</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ui-card">
        <div class="ui-card-header">WE VALUE YOUR INPUT</div>
        <p style="color:#d96c34; font-weight:600; font-size:0.9rem; margin-bottom:20px;">
            Help us improve the Academic Tracker by sharing your thoughts or reporting issues.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("feedback_form", clear_on_submit=True):
        f_name = st.text_input("Your Name (Optional)")
        f_type = st.selectbox("Feedback Type", ["Feature Request", "Bug Report", "UI/UX Improvement", "General Praise"])
        f_msg = st.text_area("Your Message", placeholder="Type your feedback here...")
        
        submitted = st.form_submit_button("Send Feedback")
        if submitted:
            if f_msg:
                # Send email directly via FormSubmit AJAX API
                import requests
                try:
                    headers = {
                        'Accept': 'application/json',
                        'Origin': 'https://academic-tracker.streamlit.app',
                        'Referer': 'https://academic-tracker.streamlit.app/'
                    }
                    # Send as JSON to match FormSubmit AJAX expectations
                    response = requests.post("https://formsubmit.co/ajax/abilash0asp@gmail.com", 
                        headers=headers, 
                        json={
                            "name": f_name if f_name else "Anonymous",
                            "type": f_type,
                            "message": f_msg,
                            "_subject": f"New Academic Tracker Feedback: {f_type}",
                            "_captcha": "false"
                        })
                    
                    if response.status_code == 200:
                        resp_data = response.json()
                        if str(resp_data.get("success", "")).lower() == "false":
                            if "Activation" in resp_data.get("message", "") or "actived" in resp_data.get("message", ""):
                                st.warning("⚠️ One-Time Activation Required! FormSubmit has just sent an email to your address. Please click 'Activate Form' in that email (check spam!) so you can receive future feedbacks.")
                            else:
                                st.error(f"FormSubmit Error: {resp_data.get('message', 'Unknown')}")
                        else:
                            st.balloons()
                            st.success("Thank you! Your feedback has been sent directly to the developer.")
                    else:
                        st.error("Failed to send feedback. Please try again later.")
                except Exception as e:
                    st.error(f"Error connecting to mail server: {e}")
            else:
                st.error("Please enter a message before submitting.")

    st.caption("UOC Academic Tracker • v2.0 • Created by Abilash")
