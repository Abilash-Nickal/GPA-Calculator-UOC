import streamlit as st
from google import genai
import pandas as pd
import json
import re
import time
from PIL import Image
import plotly.express as px
import concurrent.futures
import styles
from styles import ICON_CGPA, ICON_CREDITS, ICON_SUBJECTS, ICON_PERFORMANCE, ICON_EDIT, ICON_CALENDAR, ICON_TARGET, ICON_HELP, render_custom_metric

# ==========================================
MY_API_KEY = st.secrets["MY_API_KEY"]

# --- Page Configuration ---
st.set_page_config(
    page_title="Academic Tracker", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styles
styles.apply_styles()

def extract_gpa_from_image(image, api_key):
    """
    Extract course data from an image using Gemini Flash 2.0.
    """
    client = genai.Client(api_key=api_key)
    
    # Prompt for structured data extraction
    prompt = """
    Extract all course data from this academic results sheet.
    Provide the output in a JSON format as a list of objects.
    Each object must have: 
    - course_code (string)
    - course_title (string)
    - credits (number)
    - gpv (number)
    - grade (string)
    - academic_level (string, e.g., '1', '2', '3')
    - semester (string, e.g., '1', '2')
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, image]
        )
        
        # Parse the JSON from the response text
        text_content = response.text
        # Clean up possible markdown code blocks
        json_str = re.search(r'\[.*\]', text_content, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        return {"error": str(e)}

def process_course_data(course_list):
    """
    Process course list to handle repeats (highest GPV wins).
    """
    df = pd.DataFrame(course_list)
    
    # Simple repeat handling: keep top GPV for same course code
    # Real logic might be more complex (e.g., considering semester/year)
    if not df.empty:
        df = df.sort_values('gpv', ascending=False).drop_duplicates(subset='course_code', keep='first')
        df = df.sort_values(['academic_level', 'semester', 'course_code'])
    
    return df

# ==========================================
# SIDEBAR (App Controls & Uploads)
# ==========================================
with st.sidebar:
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1px; display:flex; align-items:center; gap:10px; text-transform:uppercase; margin-bottom:15px;">
        <div style="background:#fbe7dc; padding:6px; border-radius:6px; display:flex;">{ICON_EDIT}</div>
        Data Source
    </h3>
    """, unsafe_allow_html=True)
    st.markdown("Upload your result sheets to build the tracker.")
    
    l1_file = st.file_uploader("Level 1 Results", type=['png', 'jpg', 'jpeg'])
    l2_file = st.file_uploader("Level 2 Results", type=['png', 'jpg', 'jpeg'])
    l3_file = st.file_uploader("Level 3 Results", type=['png', 'jpg', 'jpeg'])
    
    process_btn = st.button("🚀 PROCESS DATA & VIEW DASHBOARD", use_container_width=True)
    
    st.write("---")
    
    # Social Footer
    st.markdown(f"""
    <div class="social-footer">
        <a href="https://linkedin.com" target="_blank">
            <svg viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
        </a>
        <a href="https://github.com/Abilash-Nickal" target="_blank">
            <svg viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </a>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# MAIN DASHBOARD AREA
# ==========================================
st.markdown("""
<div class="top-header">
    <div class="logo-text">ACADEMIC TRACKER</div>
</div>
<h1 class="dashboard-title">DASHBOARD OVERVIEW</h1>
<p class="dashboard-subtitle">Real-time Grade Point Average Analytics</p>
""", unsafe_allow_html=True)

if "master_data" not in st.session_state:
    st.session_state.master_data = []

# Logic to handle processing
if process_btn:
    all_data = []
    files_to_process = [("1", l1_file), ("2", l2_file), ("3", l3_file)]
    
    with st.status("🔍 Extracting intelligence from result sheets...", expanded=True) as status:
        for lvl, f in files_to_process:
            if f:
                st.write(f"Processing Level {lvl}...")
                img = Image.open(f)
                extracted = extract_gpa_from_image(img, MY_API_KEY)
                if isinstance(extracted, list):
                    all_data.extend(extracted)
                else:
                    st.error(f"Error in L{lvl}: {extracted.get('error', 'Unknown error')}")
        
        if all_data:
            df = process_course_data(all_data)
            st.session_state.master_data = df.to_dict('records')
            status.update(label="✅ intelligence extraction complete!", state="complete", expanded=False)
        else:
            status.update(label="❌ No data found. Please upload valid images.", state="error")

# Display Results
if st.session_state.master_data:
    df = pd.DataFrame(st.session_state.master_data)
    
    # Calculate Metrics
    included_df = df # Logic for repeat handling already done
    total_credits = included_df['credits'].sum()
    final_gpa = (included_df['gpv'] * included_df['credits']).sum() / total_credits if total_credits > 0 else 0
    
    # 3. TOP METRICS ROW (Column 1 equivalent from your sketch)
    m1, m2, m3 = st.columns(3)
    with m1: render_custom_metric("Final CGPA", f"{final_gpa:.4f}", "+ Active Semester", ICON_CGPA, "#d96c34")
    with m2: render_custom_metric("Total Credits", f"{int(total_credits)}", "+ Active Semester", ICON_CREDITS, "#d96c34")
    with m3: render_custom_metric("Subjects Passed", f"{len(included_df)}", "+ Active Semester", ICON_SUBJECTS, "#d96c34")
    
    st.write("---")

    # 4. TREND CHARTS & STATS
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        st.markdown('<div class="bar-chart-header">GPV DISTRIBUTION</div>', unsafe_allow_html=True)
        # GPV Distribution pie/donut chart
        gpv_counts = included_df['grade'].value_counts().reset_index()
        gpv_counts.columns = ['Grade', 'Count']
        fig_pie = px.pie(gpv_counts, values='Count', names='Grade', hole=0.6,
                        color_discrete_sequence=px.colors.sequential.Oranges_r)
        fig_pie.update_layout(
            showlegend=True, margin=dict(l=0, r=0, t=0, b=0), height=220,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1c29', size=10),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
        )
        st.markdown('<div style="background-color: rgba(253, 250, 247, 0.4); backdrop-filter: blur(10px); padding: 10px; border-radius: 0 0 2rem 2rem; border: 1px solid rgba(255, 255, 255, 0.8); border-top:none;">', unsafe_allow_html=True)
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <h4 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1px; display:flex; align-items:center; gap:10px; text-transform:uppercase; margin-bottom:15px;">
            <div style="background:#fbe7dc; padding:6px; border-radius:6px; display:flex;">{ICON_PERFORMANCE}</div>
            Top Subjects
        </h4>
        """, unsafe_allow_html=True)
        top_subjects = included_df.sort_values('gpv', ascending=False).head(5)
        st.table(top_subjects[['course_code', 'gpv', 'grade']].set_index('course_code'))

    with c2:
        st.markdown('<div class="bar-chart-header">SEMESTER-WISE GPA TREND</div>', unsafe_allow_html=True)
        # Line chart for GPA trend
        trend_df = included_df.groupby(['academic_level', 'semester']).apply(
            lambda x: (x['gpv'] * x['credits']).sum() / x['credits'].sum()
        ).reset_index(name='GPA')
        trend_df['Term'] = "L" + trend_df['academic_level'].astype(str) + " S" + trend_df['semester'].astype(str)
        
        fig_line = px.line(trend_df, x='Term', y='GPA', markers=True, color_discrete_sequence=['#d96c34'])
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1c29', size=11), margin=dict(l=10, r=10, t=25, b=10), height=380,
            xaxis=dict(showgrid=False, title="", tickfont=dict(color='#1a1c29')),
            yaxis=dict(showgrid=True, gridcolor='rgba(217, 108, 52, 0.1)', title="GPA", range=[0, 4.2], tickfont=dict(color='#1a1c29'))
        )
        st.markdown('<div style="background-color: rgba(253, 250, 247, 0.4); backdrop-filter: blur(10px); padding: 20px; border-radius: 0 0 2rem 2rem; border: 1px solid rgba(255, 255, 255, 0.8); border-top:none; box-shadow: 0 8px 30px rgba(235, 128, 68, 0.05);">', unsafe_allow_html=True)
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")

    # 5. SEMESTER BREAKDOWN CARDS
    st.markdown(f"""
    <h3 style="font-family:'Oswald', sans-serif; color:#d96c34; letter-spacing:1.5px; margin-top:30px; margin-bottom:20px; display:flex; align-items:center; gap:12px; text-transform:uppercase;">
        <div style="background:#fbe7dc; padding:8px; border-radius:8px; display:flex;">{ICON_CALENDAR}</div>
        Detailed Semester Breakdown
    </h3>
    """, unsafe_allow_html=True)
    
    sem_groups = included_df.groupby(['academic_level', 'semester'])
    for (lvl, sem), group in sem_groups:
        with st.expander(f"LEVEL {lvl} - SEMESTER {sem}"):
            st.dataframe(group[['course_code', 'course_title', 'credits', 'gpv', 'grade']], use_container_width=True, hide_index=True)

else:
    st.info("👋 Welcome! Please upload your result sheets in the sidebar to get started.")
    # Show dummy metric cards to illustrate layout
    m1, m2, m3 = st.columns(3)
    with m1: render_custom_metric("Final CGPA", "0.0000", "Sample Data", ICON_CGPA, "#cccccc")
    with m2: render_custom_metric("Total Credits", "0", "Sample Data", ICON_CREDITS, "#cccccc")
    with m3: render_custom_metric("Subjects Passed", "0", "Sample Data", ICON_SUBJECTS, "#cccccc")
