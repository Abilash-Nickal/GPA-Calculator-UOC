import streamlit as st
import streamlit.components.v1 as components

# --- ADS CONFIGURATION ---
# You can update these in your .streamlit/secrets.toml file:
# [monetization]
# adsense_publisher_id = "pub-xxxxxxxxxxxxxxxx"
# adsense_slot_sidebar = "xxxxxxxxxx"
# adsense_slot_footer = "xxxxxxxxxx"
# bmac_user = "yourusername"

def get_ads_config():
    """Retrieve ad configuration from secrets, with sensible defaults."""
    try:
        return st.secrets.get("monetization", {})
    except:
        return {}

def render_adsense_unit(publisher_id, slot_id, format="auto", responsive="true"):
    """Renders a Google AdSense unit using an iframe-friendly script."""
    ad_html = f"""
    <div style="text-align:center; margin: 10px 0;">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-{publisher_id}"
             crossorigin="anonymous"></script>
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-{publisher_id}"
             data-ad-slot="{slot_id}"
             data-ad-format="{format}"
             data-full-width-responsive="{responsive}"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({{}});
        </script>
    </div>
    """
    # Adjust height based on format
    height = 280 if format == "auto" else 100
    components.html(ad_html, height=height)

def render_sidebar_ad():
    """Renders an ad unit specifically for the sidebar."""
    config = get_ads_config()
    pub_id = config.get("adsense_publisher_id")
    slot_id = config.get("adsense_slot_sidebar")
    
    st.markdown("<hr style='margin: 20px 0 10px 0; opacity: 0.1;'/>", unsafe_allow_html=True)
    
    if pub_id and slot_id:
        st.caption("✨ Sponsored")
        render_adsense_unit(pub_id, slot_id)
    else:
        # Default placeholder/Sponsorship if no AdSense is configured
        render_sponsor_card_mini()

def render_footer_ad():
    """Renders a wide horizontal ad unit for the bottom of pages."""
    config = get_ads_config()
    pub_id = config.get("adsense_publisher_id")
    slot_id = config.get("adsense_slot_footer")
    
    st.write("---")
    if pub_id and slot_id:
        st.caption("✨ Sponsored Content")
        render_adsense_unit(pub_id, slot_id, format="horizontal")
    else:
        # Simple attribution / support footer
        st.markdown("""
        <div style="text-align:center; padding: 20px; opacity: 0.6; font-size: 0.8rem;">
            Proudly supporting students of <b>University of Colombo</b>. <br/>
            Enjoying the app? Consider sharing it with your friends!
        </div>
        """, unsafe_allow_html=True)

def render_sponsor_card_mini():
    """A small premium-styled card for the sidebar to encourage support."""
    bmac_user = get_ads_config().get("bmac_user", "abilash")
    html = f"""
    <div class="sidebar-sponsor-card">
        <div style="font-size: 0.7rem; color: #8c8f9c; letter-spacing: 1px; margin-bottom: 8px;">SUPPORT THE PROJECT</div>
        <div style="font-weight: 700; color: #d96c34; font-size: 0.9rem; margin-bottom: 12px;">Keep Tracker Free!</div>
        <a href="https://www.buymeacoffee.com/{bmac_user}" target="_blank" style="text-decoration: none;">
            <div class="bmac-button">
                <img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" alt="BMC" style="width: 15px; margin-right: 8px;">
                <span>Buy me a coffee</span>
            </div>
        </a>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_featured_sponsor_section():
    """A larger section for the Help/Feedback page."""
    st.markdown("""
    <div class="ui-card" style="background: linear-gradient(135deg, rgba(217, 108, 52, 0.05) 0%, rgba(217, 108, 52, 0.1) 100%); border: 1px dashed #d96c34;">
        <div class="ui-card-header">SUPPORT THE DEVELOPER</div>
        <div style="padding: 10px;">
            <h3 style="color:#d96c34; font-family:'Oswald',sans-serif; margin-bottom:10px;">KEEP THIS SERVICE ONLINE</h3>
            <p style="font-size:0.9rem; line-height:1.5;">
                This app is developed and maintained for free to help fellow <b>UOC</b> students. 
                Running cloud servers and maintenance costs money. If this tracker helped you, 
                consider a small contribution to keep it running!
            </p>
            <div style="display:flex; gap:15px; margin-top:20px;">
                <a href="https://www.buymeacoffee.com/abilash" target="_blank" style="text-decoration:none;">
                    <div style="background:#FFDD00; color:#000000; padding:10px 20px; border-radius:10px; font-weight:700; display:flex; align-items:center; gap:10px; font-size:0.9rem;">
                        <img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" width="20">
                        Buy Me A Coffee
                    </div>
                </a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
