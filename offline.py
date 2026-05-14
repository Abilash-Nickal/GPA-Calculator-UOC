import streamlit as st

# The new Vercel link
new_url = "https://gpa-calculator-uoc.vercel.app"

# Hide the default Streamlit menu and footer for a cleaner look during the split-second redirect
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Inject JavaScript to handle the instant redirect
# Using .replace() ensures the old Streamlit link isn't saved in the user's "Back" button history
redirect_code = f"""
<meta http-equiv="refresh" content="0; url={new_url}">
<script>
    window.location.replace("{new_url}");
</script>
"""
st.markdown(redirect_code, unsafe_allow_html=True)

# A fallback message just in case the user's browser blocks automatic JavaScript/HTML redirects
st.info(f"The GPA Calculator has moved! If you aren't redirected instantly, [click here to go to the new site]({new_url}).")
