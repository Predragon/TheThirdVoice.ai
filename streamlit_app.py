import streamlit as st  
import google.generativeai as genai  
import json  
from typing import Dict  
import uuid  
import datetime  
  
# --- Beta Tester Token Validation ---  
valid_tokens = ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]  
if 'token_validated' not in st.session_state:  
    st.session_state.token_validated = False  
  
if not st.session_state.token_validated:  
    with st.form("token_form"):  
        st.markdown("### Welcome to The Third Voice Beta")  
        token_input = st.text_input("Enter Beta Tester Token:", type="password", help="Contact hello@thethirdvoice.ai for a token.")  
        submit_token = st.form_submit_button("Validate Token")  
        if submit_token:  
            if token_input in valid_tokens:  
                st.session_state.token_validated = True  
                st.success("✅ Token validated! Welcome to The Third Voice beta.")  
                st.rerun()  
            else:  
                st.error("❌ Invalid token. Please contact hello@thethirdvoice.ai.")  
    st.stop()  
  
# --- Configuration and Setup ---  
st.set_page_config(  
    page_title="The Third Voice",  
    page_icon="🎙️",  
    layout="wide",  
    initial_sidebar_state="collapsed"  
)  
  
# --- Custom CSS ---  
st.markdown("""  
<style>  
    .main-header {  
        text-align: center;  
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);  
        color: white;  
        padding: 2rem;  
        border-radius: 10px;  
        margin-bottom: 2rem;  
    }  
    .feature-card { border: 2px solid #e0e0e0; border-radius: 10px; padding: 1.5rem; margin: 1rem 0; background: #f9f9f9; }  
    .ai-response { background: #f0f8ff; border-left: 4px solid #4CAF50; padding: 1rem; margin: 1rem 0; border-radius: 5px; }  
    .warning-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin: 1rem 0; border-radius: 5px; }  
    .emotion-card { background: #e8f5e8; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #4CAF50; }  
    .sentiment-positive { background: #d4edda; color: #155724; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #28a745; }  
    .sentiment-negative { background: #f8d7da; color: #721c24; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #dc3545; }  
    .sentiment-neutral { background: #d1ecf1; color: #0c5460; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #17a2b8; }  
</style>  
""", unsafe_allow_html=True)  
  
# --- API Key Initialization ---  
api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", "")  
if 'gemini_api_key' not in st.session_state:  
    st.session_state.gemini_api_key = api_key_from_secrets  
  
api_key_loaded = bool(st.session_state.gemini_api_key)  
  
# --- API Key Configuration UI ---  
if not api_key_loaded:  
    with st.expander("🔑 Configure Google Gemini API", expanded=True):  
        st.markdown("**Get your free API key from:** [Google AI Studio](https://aistudio.google.com/app/apikey)")  
        api_key_input = st.text_input(  
            "Enter your Gemini API key:",  
            value="",  
            type="password",  
            help="Your API key will be stored only in session memory."  
        )  
        if st.button("Save API Key"):  
            if api_key_input:  
                try:  
                    genai.configure(api_key=api_key_input)  
                    test_model = genai.GenerativeModel('gemini-1.5-flash')  
                    test_model.generate_content("Test")  
                    st.session_state.gemini_api_key = api_key_input  
                    st.success("✅ API key saved and validated! You can now use all AI features.")  
                    st.rerun()  
                except Exception as e:  
                    st.error(f"❌ Failed to validate API key: {e}")  
            else:  
                st.warning("⚠️ Please enter a valid API key.")  
  
# --- GeminiMessageCoach Class ---
# (Code for GeminiMessageCoach not shown here to keep it concise — your original class remains unchanged)

# --- App Session State ---  
if 'usage_count' not in st.session_state:  
    st.session_state.usage_count = 0  
if 'history' not in st.session_state:  
    st.session_state.history = []  
  
@st.cache_resource  
def get_ai_coach(api_key):  
    return GeminiMessageCoach(api_key)  
  
ai_coach = get_ai_coach(st.session_state.gemini_api_key)  
  
# --- App Header ---  
st.markdown("""  
<div class="main-header">  
    <h1>🎙️ The Third Voice</h1>  
    <h3>Your AI co-mediator for emotionally intelligent communication</h3>  
    <p><i>Built in detention, with a phone, for life's hardest moments.</i></p>  
    <p>⚡ <strong>Powered by Google Gemini Flash</strong></p>  
</div>  
""", unsafe_allow_html=True)  
  
# --- Sidebar ---  
st.sidebar.markdown(f"**API Calls Used:** {st.session_state.usage_count}/1500 daily")  
st.sidebar.info("Welcome to The Third Voice beta! Analyze messages, save history locally, and share feedback at hello@thethirdvoice.ai.")  
  
# --- Tabs ---
# (Code for tab1 to tab4 remains unchanged)

# --- Final block inside tab5 with fixed "with st" ---
with tab5:
    st.markdown("### 📜 Conversation History")
    uploaded_file = st.file_uploader("Upload Saved History (optional)", type="json", help="Upload your saved history file to continue a conversation. Max 1MB.", accept_multiple_files=False)
    history_data = st.session_state.history
    if uploaded_file:
        try:
            history_data = json.load(uploaded_file)
            st.success("✅ History uploaded! Select a conversation below.")
        except:
            st.error("❌ Invalid history file. Please upload a valid JSON file.")

    if history_data:
        conversation_options = [f"[{entry['timestamp']}] {entry['context']}: {entry['original'][:50]}..." for entry in history_data]
        selected_conversation = st.selectbox("Select a conversation to continue:", ["None"] + conversation_options)
        if selected_conversation != "None":
            selected_index = conversation_options.index(selected_conversation)
            selected_entry = history_data[selected_index]
            st.markdown(f"**Selected Conversation ({selected_entry['context']}):**")
            st.markdown(f"**Original:** {selected_entry['original']}")
            st.markdown(f"**Sentiment:** {selected_entry['sentiment'].title()}")
            st.markdown(f"**Reframed:** {selected_entry['reframed']}")
            new_message = st.text_area("Reply to this conversation:", placeholder="Type your next message...", height=100)
            context = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace"], index=["general", "romantic", "coparenting", "workplace"].index(selected_entry['context']) if selected_entry['context'] in ["general", "romantic", "coparenting", "workplace"] else 0)
            if st.button("⚡ Analyze & Reframe Reply", type="primary"):
                if new_message.strip():
                    with st.spinner("Analyzing and reframing your reply..."):
                        st.session_state.usage_count += 1
                        analysis_result = ai_coach.analyze_message(new_message, history_context)
                        reframed = ai_coach.reframe_message(new_message, context, history_context)
                        st.markdown("#### ⚡ AI Response")
                        st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                        st.markdown(reframed)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.code(reframed, language="text")
                        st.session_state.history.append({
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "original": new_message,
                            "context": context,
                            "sentiment": analysis_result.get("sentiment", "neutral"),
                            "reframed": reframed
                        })
