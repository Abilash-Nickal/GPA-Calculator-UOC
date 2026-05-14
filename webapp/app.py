import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import logic
import pandas as pd

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process_data', methods=['POST'])
def process_data():
    try:
        data = request.json
        raw_text = data.get('raw_text', '')
        if not raw_text:
            return jsonify({'success': False, 'error': 'Empty input'})
            
        parsed_data = logic.parse_pasted_data(raw_text)
        if not parsed_data:
            return jsonify({'success': False, 'error': 'No valid course data found.'})
            
        # Optional: Combine with existing data if passed
        existing_data = data.get('existing_data', [])
        total_data = existing_data + parsed_data
        
        df_final, error = logic.process_combined_data(total_data)
        
        if error:
            return jsonify({'success': False, 'error': error})
            
        # Convert DataFrame to list of dicts to return
        records = df_final.to_dict(orient='records')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recalculate', methods=['POST'])
def recalculate():
    try:
        data = request.json
        raw_records = data.get('data', [])
        if not raw_records:
            return jsonify({'success': True, 'data': []})
        
        # We process combined data again to recalculate based on updated values (like include/exclude)
        # Note: we might just accept the modified dataframe directly from frontend without full reprocessing 
        # but to be safe and cap repeating GPV, we can run logic.process_combined_data if needed, 
        # OR simply return success as frontend does the math.
        # Since frontend math might be complex, let's just use Python for metrics.
        df = pd.DataFrame(raw_records)
        df['credits'] = pd.to_numeric(df['credits'], errors='coerce').fillna(0)
        df['gpv'] = pd.to_numeric(df['gpv'], errors='coerce').fillna(0)
        
        # Get included
        included_df = df[df['Include'] == True]
        
        total_credits = included_df['credits'].sum()
        total_gp = (included_df['credits'] * included_df['gpv']).sum()
        final_gpa = total_gp / total_credits if total_credits > 0 else 0.0
        
        classification = logic.get_classification(final_gpa)
        
        return jsonify({
            'success': True, 
            'metrics': {
                'total_credits': int(total_credits),
                'final_gpa': round(final_gpa, 4),
                'subjects_passed': len(included_df),
                'classification': classification
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save', methods=['POST'])
def save():
    try:
        data = request.json
        user_id = data.get('user_id')
        payload = data.get('payload') # contains data, target_class, total_deg_credits
        
        if not payload:
            return jsonify({'success': False, 'error': 'No payload provided'})
            
        if not user_id:
             return jsonify({'success': False, 'error': 'No user_id provided'})

        success, msg = logic.universal_save(payload, user_id)
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load', methods=['GET'])
def load():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'No user_id provided'})
            
        payload, msg = logic.universal_load(user_id)
        if payload is not None:
             return jsonify({'success': True, 'payload': payload, 'message': msg})
        else:
             return jsonify({'success': False, 'error': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
