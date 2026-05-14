import re
import pandas as pd
import json
import os
from supabase import create_client

def parse_pasted_data(raw_text):
    """Parses raw text from the university portal using regex."""
    if not raw_text.strip(): return []
    # Pre-filter to remove headers/footers as requested by the user
    lines = raw_text.split('\n')
    filtered_lines = []
    for line in lines:
        l = line.strip().upper()
        if not l: continue
        # Ignore Table Headers, Level Headers, and Course Count Footers
        if 'COURSE UNIT' in l and 'COURSE TITLE' in l: continue
        if l.startswith('LEVEL') and len(l.split()) <= 2: continue
        if 'NO. OF COURSES' in l: continue
        filtered_lines.append(line)
    
    clean_text = '\n'.join(filtered_lines)
    parsed_data = []

    # This pattern matches the specific format of the university portal results
    # Updated to handle leading ID/Level, Medical registry type, 'mc' grade, and optional trailing dot.
    squish_pattern = r'(?:[\d\s]+)?([A-Z]{2,3}\s\d{4})\s*(.*?)\s*(\d)\s*(Standard|Repeat|Medical)\s*(\d{4})\s*(\d)\s*(Official results released\.?|Marks Confirmed\.?)\s*(mc|ab|[A-Z][+-]?|--)?\s*(\d\.\d{2}|--)?'
    matches = list(re.finditer(squish_pattern, clean_text, re.IGNORECASE))
    if matches:
        for match in matches:
            # GPV might be missing for some grades or specially marked
            gpv_val = 0.0
            if match.group(9) and match.group(9) != '--':
                try:
                    gpv_val = float(match.group(9))
                except ValueError:
                    gpv_val = 0.0

            try:
                parsed_data.append({
                    "course_code": match.group(1).strip(), 
                    "course_title": match.group(2).strip(),
                    "credits": int(match.group(3)), 
                    "registered_type": match.group(4),
                    "semester": match.group(6), 
                    "grade": match.group(8) if match.group(8) else "--",
                    "gpv": gpv_val
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
        
        # Capping only applies to 'Repeat' registration types
        is_repeat_type = str(best_row.get('registered_type', '')).lower() == 'repeat'
        
        # Determine if the course should be included in GPA calculations
        # According to user request: ignore if the grade is empty (--)
        grade_val = str(best_row.get('grade', '--')).strip()
        best_row['Include'] = True if grade_val != "--" else False
        
        if is_repeat_type:
            # According to university rules, repeat passes are capped at C (2.0)
            if best_row['gpv'] > 2.0:
                best_row['original_gpv'] = best_row['gpv']
                best_row['gpv'] = 2.0 
                best_row['Remarks'] = 'Repeated (Capped C)'
            else:
                best_row['Remarks'] = 'Repeated'
        elif any(group['registered_type'].astype(str).str.contains('Medical', case=False, na=False)):
            best_row['Remarks'] = 'Medical'
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
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except Exception as e:
        print(f"Supabase Connection Failed: {e}")
    return None

def universal_save(payload, user_id):
    """Saves DataFrame and Target Settings to Supabase."""
    conn = init_supabase()
    if conn:
        try:
            # Upsert into Supabase
            conn.table("gpa_records").upsert(
                {"user_id": user_id, "gpa_json": payload}
            ).execute()
            return True, "Cloud Save Successful"
        except Exception as e:
            return False, f"Cloud Error: {e}"
    else:
        return False, "Cloud Connection Failed"

def universal_load(user_id):
    """Loads DataFrame and restores Target Settings from Supabase."""
    conn = init_supabase()
    if conn:
        try:
            result = conn.table("gpa_records").select("gpa_json").eq("user_id", user_id).execute()
            if result.data and len(result.data) > 0:
                raw_payload = result.data[0].get("gpa_json", {})
                return raw_payload, "Loaded from Cloud"
        except Exception as e:
            print(f"Cloud load error: {e}")
            pass
    return None, "No cloud data found"

