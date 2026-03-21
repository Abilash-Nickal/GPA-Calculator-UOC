import re
import pandas as pd

def parse_pasted_data(raw_text):
    """Parses raw text from the university portal using regex."""
    if not raw_text.strip(): return []
    parsed_data = []
    # This pattern matches the specific format of the university portal results
    squish_pattern = r'([A-Z]{2,3}\s\d{4})\s*(.*?)\s*(\d)\s*(Standard|Repeat)\s*(\d{4})\s*(\d)\s*(Official results released\.|Marks Confirmed\.)\s*([A-Z][+-]?|ab|--)?\s*(\d\.\d{2}|--)?'
    matches = list(re.finditer(squish_pattern, raw_text, re.IGNORECASE))
    if matches:
        for match in matches:
            if match.group(9) and match.group(9) != '--':
                try:
                    parsed_data.append({
                        "course_code": match.group(1).strip(), 
                        "course_title": match.group(2).strip(),
                        "credits": int(match.group(3)), 
                        "registered_type": match.group(4),
                        "semester": match.group(6), 
                        "grade": match.group(8) if match.group(8) else "--",
                        "gpv": float(match.group(9))
                    })
                except Exception: 
                    pass
    return parsed_data

def get_academic_level(course_code):
    """Extracts the academic level (year) from a course code."""
    match = re.search(r'\d', str(course_code))
    return match.group(0) if match else "1"

def process_combined_data(all_data):
    """Combines and processes raw course data, handling repeats and capping GPV."""
    if not all_data: return None, "No valid course data found."
    df = pd.DataFrame(all_data)
    df['credits'] = pd.to_numeric(df['credits'], errors='coerce')
    df['gpv'] = pd.to_numeric(df['gpv'], errors='coerce')
    if 'semester' not in df.columns: df['semester'] = "1"
    df['semester'] = df['semester'].astype(str)
    df['academic_level'] = df['course_code'].apply(get_academic_level)
    df = df.dropna(subset=['credits', 'gpv'])
    
    final_rows = []
    # Group by course code to handle repeat attempts
    for code, group in df.groupby('course_code'):
        # Keep the attempt with the highest GPV
        best_idx = group['gpv'].idxmax()
        best_row = group.loc[best_idx].copy()
        
        # Check if the course was repeated
        is_repeat = (len(group) > 1) or any(group['registered_type'].astype(str).str.contains('Repeat', case=False, na=False))
        best_row['Include'] = True 
        
        if is_repeat:
            # According to university rules, repeat passes are capped at C (2.0)
            if best_row['gpv'] > 2.0:
                best_row['original_gpv'] = best_row['gpv']
                best_row['gpv'] = 2.0 
                best_row['Remarks'] = 'Repeated (Capped C)'
            else:
                best_row['Remarks'] = 'Repeated'
        else:
            best_row['Remarks'] = 'Standard'
        final_rows.append(best_row)
        
    df_final = pd.DataFrame(final_rows)
    df_final = df_final.sort_values(by=['academic_level', 'semester', 'course_code']).reset_index(drop=True)
    return df_final, None

def get_classification(cgpa):
    """Returns the degree classification based on University of Colombo rules."""
    if cgpa >= 3.70: return "FIRST CLASS"
    if cgpa >= 3.30: return "2ND UPPER"
    if cgpa >= 3.00: return "2ND LOWER"
    return "GENERAL"

def calculate_target_required_gpa(target_gpa, current_gpa, current_credits, total_credits):
    """Calculates the average GPA required in remaining credits to reach a target CGPA."""
    remaining_credits = total_credits - current_credits
    if remaining_credits <= 0: 
        return None
    # Formula: (Target * Total - Current * CurrentCredits) / RemainingCredits
    required_gp = (target_gpa * total_credits) - (current_gpa * current_credits)
    required_avg = required_gp / remaining_credits
    return required_avg

def init_supabase():
    import streamlit as st
    try:
        from st_supabase_connection import SupabaseConnection
        return st.connection("supabase", type=SupabaseConnection)
    except Exception as e:
        try:
            # Direct client fallback using secrets
            from supabase import create_client
            conf = st.secrets.get("connections", {}).get("supabase", {})
            url = conf.get("url") or conf.get("SUPABASE_URL")
            key = conf.get("key") or conf.get("SUPABASE_KEY")
            if url and key:
                return create_client(url, key)
        except Exception as e2:
            st.error(f"Supabase Connection Failed: {e2}")
        return None

def universal_save(df, user_id=None):
    """Saves DataFrame locally or to Supabase depending on auth status."""
    import json
    import streamlit as st
    from streamlit_local_storage import LocalStorage
    
    if df is None:
        return False, "No data to save"
        
    data_json = df.to_json(orient="records")
    
    if user_id:
        conn = init_supabase()
        if conn:
            try:
                # Upsert into Supabase
                conn.table("gpa_records").upsert(
                    {"user_id": user_id, "gpa_json": json.loads(data_json)}
                ).execute()
                return True, "Cloud Save Successful"
            except Exception as e:
                return False, f"Cloud Error: {e}"
        else:
            return False, "Cloud Connection Failed"
    else:
        # Local save
        localS = LocalStorage()
        localS.setItem("guest_gpa_data", data_json)
        return True, "Local Save Successful"

def universal_load(user_id=None):
    """Loads DataFrame from local storage or Supabase.
    
    If user_id is provided (logged-in user), ONLY loads from cloud.
    Never falls back to localStorage for logged-in users to prevent
    data leakage between users sharing the same browser.
    If no user_id (guest), loads from localStorage only.
    """
    import pandas as pd
    import json
    import streamlit as st
    from streamlit_local_storage import LocalStorage
    
    if user_id:
        # Logged-in user: ONLY load from cloud, never fall back to localStorage
        conn = init_supabase()
        if conn:
            try:
                result = conn.table("gpa_records").select("gpa_json").eq("user_id", user_id).execute()
                if result.data and len(result.data) > 0:
                    json_data = result.data[0].get("gpa_json", [])
                    return pd.DataFrame(json_data), "Loaded from Cloud"
            except Exception as e:
                pass
        # Cloud failed or no data — return empty, do NOT leak localStorage
        return None, "No cloud data found"
    
    # Guest user: load from localStorage only
    localS = LocalStorage()
    local_data = localS.getItem("guest_gpa_data")
    if local_data:
        try:
            return pd.read_json(local_data), "Loaded Locally"
        except:
            pass
            
    return None, "No data found"
