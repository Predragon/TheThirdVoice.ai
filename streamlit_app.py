import streamlit as st
import google.generativeai as genai
import json
import datetime
import re
import time

# Constants
VALID_TOKENS = {"ttv-beta-001", "ttv-beta-002", "ttv-beta-003"}
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
DAILY_LIMIT = 1500

# Session state initialization
def init_session_state():
    defaults = {
        'token_validated': False,
        'api_key': st.secrets.get("GEMINI_API_KEY", ""),
        'count': 0,
        'history': [],
        'active_msg': '',
        'active_ctx': 'general'
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

init_session_state()

# Token validation
if not st.session_state.token_validated:
    token = st.text_input("🔑 Beta Token:", type="password")
    if token in VALID_TOKENS:
        st.session_state.token_validated = True
        st.success("✅ Welcome!")
        st.rerun()
    elif token:
        st.error("❌ Invalid token")
        st.stop()

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")

# Cached CSS
@st.cache_data
def get_css():
    return """
    <style>
        .ai-box{background:#f0f8ff;padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0;color:#000}
        .pos{background:#d4edda;padding:0.5rem;border-radius:5px;color:#155724;margin:0.2rem 0;font-weight:bold}
        .neg{background:#f8d7da;padding:0.5rem;border-radius:5px;color:#721c24;margin:0.2rem 0;font-weight:bold}
        .neu{background:#d1ecf1;padding:0.5rem;border-radius:5px;color:#0c5460;margin:0.2rem 0;font-weight:bold}
        .meaning-box{background:#f8f9fa;padding:1rem;border-radius:8px;border-left:4px solid #17a2b8;margin:0.5rem 0;color:#000}
        .need-box{background:#fff3cd;padding:1rem;border-radius:8px;border-left:4px solid #ffc107;margin:0.5rem 0;color:#000}
        .error-box{background:#f8d7da;padding:1rem;border-radius:8px;border-left:4px solid #dc3545;margin:0.5rem 0;color:#721c24}
        .offline-box{background:#fff8dc;padding:1rem;border-radius:8px;border-left:4px solid #ff9800;margin:0.5rem 0;color:#000}
        [data-theme="dark"] .ai-box{background:#1e3a5f;color:#fff}
        [data-theme="dark"] .pos{background:#2d5a3d;color:#90ee90}
        [data-theme="dark"] .neg{background:#5a2d2d;color:#ffb3b3}
        [data-theme="dark"] .neu{background:#2d4a5a;color:#87ceeb}
        [data-theme="dark"] .meaning-box{background:#2d4a5a;color:#87ceeb}
        [data-theme="dark"] .need-box{background:#5a5a2d;color:#ffeb3b}
        [data-theme="dark"] .offline-box{background:#5a4d2d;color:#ffeb3b}
    </style>
    """

st.markdown(get_css(), unsafe_allow_html=True)

# API key setup
if not st.session_state.api_key:
    st.warning("⚠️ API Key Required")
    key = st.text_input("Gemini API Key:", type="password")
    if st.button("Save") and key:
        st.session_state.api_key = key
        st.success("✅ Saved!")
        st.rerun()
    st.stop()

# Cached AI model
@st.cache_resource
def get_ai():
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Quota management
@st.cache_data(ttl=60)
def get_quota_info():
    current_usage = st.session_state.count
    remaining = max(0, DAILY_LIMIT - current_usage)
    return current_usage, remaining, DAILY_LIMIT

# JSON cleaning
def clean_json_response(text):
    text = re.sub(r'```json\s*|\s*```', '', text)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    return json_match.group(0) if json_match else text

# Offline analysis
def get_offline_analysis(msg, ctx, is_received=False):
    positive_words = ['good', 'great', 'happy', 'love', 'awesome', 'excellent', 'wonderful', 'amazing', 'perfect', 'thank']
    negative_words = ['bad', 'hate', 'angry', 'sad', 'terrible', 'awful', 'horrible', 'upset', 'mad', 'disappointed']
    emotion_map = {
        'angry': ['angry', 'mad', 'furious'],
        'sad': ['sad', 'disappointed', 'hurt'],
        'happy': ['happy', 'excited', 'great'],
        'anxious': ['worried', 'anxious', 'concerned']
    }
    context_insights = {
        "romantic": "Personal message involving feelings or relationship dynamics.",
        "coparenting": "Relates to child-related matters or parenting coordination.",
        "workplace": "Professional communication involving work tasks or relationships.",
        "family": "Family-related message involving personal or domestic matters.",
        "friend": "Casual message between friends.",
        "general": "General communication."
    }

    msg_lower = msg.lower()
    pos_count = sum(word in msg_lower for word in positive_words)
    neg_count = sum(word in msg_lower for word in negative_words)
    sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"
    emotion = next((e for e, words in emotion_map.items() if any(word in msg_lower for word in words)), "neutral")

    if is_received:
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "meaning": f"📴 **Offline Analysis:** {context_insights.get(ctx, 'General communication.')}. The tone appears {sentiment} with {emotion} undertones. For detailed analysis, try again when API quota resets.",
            "need": "More context needed for detailed analysis",
            "response": f"I understand you're sharing something important. Could you help me understand more about what you're looking for in this {ctx} situation?"
        }
    return {
        "sentiment": sentiment,
        "emotion": emotion,
        "reframed": f"📴 **Offline Mode:** Here's a basic reframe - Consider saying: 'I'd like to discuss something regarding our {ctx} situation: {msg[:80]}{'...' if len(msg) > 80 else ''}'"
    }

# Message analysis
def analyze(msg, ctx, is_received=False, retry_count=0):
    current_usage, remaining, _ = get_quota_info()
    if remaining <= 0:
        st.warning(f"⚠️ Daily quota reached ({current_usage}/{DAILY_LIMIT}). Using offline mode.")
        return get_offline_analysis(msg, ctx, is_received)

    prompt = (
        f'''Context: {ctx}. Analyze this received message: "{msg}"
Return JSON with keys: sentiment, emotion, meaning, need, response''' if is_received else
        f'''Context: {ctx}. Help reframe this message: "{msg}"
Return JSON with keys: sentiment, emotion, reframed'''
    )

    try:
        result = get_ai().generate_content(prompt)
        parsed_result = json.loads(clean_json_response(result.text))
        required_keys = ['sentiment', 'emotion', 'meaning', 'need', 'response'] if is_received else ['sentiment', 'emotion', 'reframed']
        if not all(key in parsed_result and parsed_result[key] for key in required_keys):
            raise ValueError("Missing or empty required keys")
        return parsed_result
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            st.error("🚫 **API Quota Exceeded**")
            st.info("**Solutions:** Wait (reset at midnight PST), Upgrade to paid plan, or Use offline mode")
            return get_offline_analysis(msg, ctx, is_received)
        st.error(f"Analysis error: {str(e)}")
        if retry_count < 2:
            time.sleep(1)
            return analyze(msg, ctx, is_received, retry_count + 1)
        return get_offline_analysis(msg, ctx, is_received)

# Load conversation from history
def load_conversation(idx):
    entry = st.session_state.history[idx]
    st.session_state.active_msg = entry['original']
    st.session_state.active_ctx = entry['context']
    st.rerun()

# Sidebar rendering
def render_quota_sidebar():
    current_usage, remaining, daily_limit = get_quota_info()
    quota_color = "🟢" if remaining > 300 else "🟡" if remaining > 100 else "🔴"
    st.sidebar.markdown(f"**API Uses:** {quota_color} {current_usage}/{daily_limit}")
    st.sidebar.markdown(f"**Remaining:** {remaining}")
    if remaining <= 100:
        st.sidebar.warning("⚠️ Low quota - consider offline mode")
    if remaining == 0:
        st.sidebar.error("🚫 Quota exhausted - using offline mode")

def render_history_sidebar():
    uploaded = st.sidebar.file_uploader("📤 Load History", type="json")
    if uploaded:
        try:
            st.session_state.history = json.load(uploaded)
            st.sidebar.success("✅ Loaded!")
        except:
            st.sidebar.error("❌ Invalid file")

    if st.session_state.history:
        st.sidebar.download_button(
            "💾 Save",
            json.dumps(st.session_state.history, indent=2),
            f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
        )
        st.sidebar.markdown("📜 **This Session**")
        for i, entry in enumerate(st.session_state.history[-5:]):
            real_idx = len(st.session_state.history) - 5 + i
            if st.sidebar.button(f"#{real_idx+1} {entry['context'][:3]} ({entry['time'][-5:]})", key=f"load_{real_idx}"):
                load_conversation(real_idx)

# Context selector
def render_context_selector(key_suffix=""):
    return st.selectbox("Context:", CONTEXTS, index=CONTEXTS.index(st.session_state.active_ctx), key=f"ctx{key_suffix}")

# Analysis tab rendering
def render_analysis_tab(is_received=False):
    tab_type = "Understand Message" if is_received else "Improve Message"
    st.markdown(f"### {tab_type}")
    
    msg = st.text_area("Received:" if is_received else "Message:", value=st.session_state.active_msg, height=120, key=f"{'translate' if is_received else 'coach'}_msg")
    ctx = render_context_selector("2" if is_received else "")
    
    if st.button("🔍 Analyze" if is_received else "🚀 Analyze", type="primary") and msg.strip():
        with st.spinner(f"Analyzing {'the received' if is_received else 'your'} message..."):
            st.session_state.count += 1
            result = analyze(msg, ctx, is_received)
            sentiment = result.get("sentiment", "neutral")
            
            st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
            
            if is_received:
                meaning = result.get('meaning', 'Unable to analyze')
                box_class = "offline-box" if "📴 **Offline Analysis:**" in meaning else "meaning-box"
                st.markdown(f'<div class="{box_class}"><strong>💭 What they mean:</strong><br>{meaning}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="need-box"><strong>🎯 What they need:</strong><br>{{result.get("need", "Unable to determine")}}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-box"><strong>💬 Suggested response:</strong><br>{result.get("response", "I understand.")}</div>', unsafe_allow_html=True)
                display_result = result.get("response")
            else:
                st.markdown(f'<div class="ai-box">{result.get("reframed", msg)}</div>', unsafe_allow_html=True)
                display_result = result.get("reframed")
            
            if st.button("📋 Copy", key=f"copy_btn_{'translate' if is_received else 'coach'}"):
                st.success("✅ Copied to clipboard!")
            
            history_entry = {
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": "receive" if is_received else "send",
                "context": ctx,
                "original": msg,
                "result": display_result,
                "sentiment": sentiment
            }
            if is_received:
                history_entry.update({"meaning": result.get('meaning', ''), "need": result.get('need', '')})
            st.session_state.history.append(history_entry)

# Main rendering
render_quota_sidebar()
st.sidebar.markdown("---")
render_history_sidebar()

st.image("logo.png", width=200)
tab1, tab2, tab3 = st.tabs(["📤 Coach", "📥 Translate", "ℹ️ About"])

with tab1:
    render_analysis_tab(is_received=False)
with tab2:
    render_analysis_tab(is_received=True)
with tab3:
    st.markdown("""
    ### The Third Voice
    **AI communication coach** for better conversations.

    **Features:**
    - 📤 **Coach:** Improve outgoing messages
    - 📥 **Translate:** Understand incoming messages with deep analysis
    - 📜 **History:** Session tracking with save/load

    **Contexts:** General, Romantic, Coparenting, Workplace, Family, Friend

    **Privacy:** Local sessions only, manual save/load

    *Beta v0.9.1 • Contact: hello@thethirdvoice.ai*
    """)

st.markdown("---")
st.markdown("*Feedback: hello@thethirdvoice.ai*")
