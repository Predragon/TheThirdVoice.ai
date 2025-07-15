import streamlit as st
import google.generativeai as genai
import json
import datetime
import re
import time

# --- Helper Functions ---

def init_sess_state_defaults(defaults: dict):
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

@st.cache_data
def get_css():
    return """<style>
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

/* Full width tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    width: 100%;
    justify-content: stretch;
}

.stTabs [data-baseweb="tab"] {
    flex: 1;
    text-align: center;
}

.stTabs [data-baseweb="tab-panel"] {
    padding: 20px;
    min-height: 70vh;
}
</style>"""

@st.cache_data(ttl=60)
def get_quota_info():
    daily_limit = 1500
    current_usage = st.session_state.count
    remaining = max(0, daily_limit - current_usage)
    return current_usage, remaining, daily_limit

@st.cache_resource
def get_ai(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def get_offline_analysis(msg, ctx, is_received=False):
    positive_words = ['good', 'great', 'happy', 'love', 'awesome', 'excellent', 'wonderful', 'amazing', 'perfect', 'thank']
    negative_words = ['bad', 'hate', 'angry', 'sad', 'terrible', 'awful', 'horrible', 'upset', 'mad', 'disappointed']

    msg_lower = msg.lower()
    pos_count = sum(word in msg_lower for word in positive_words)
    neg_count = sum(word in msg_lower for word in negative_words)

    sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"

    emotion_map = {
        'angry': ['angry', 'mad', 'furious'],
        'sad': ['sad', 'disappointed', 'hurt'],
        'happy': ['happy', 'excited', 'great'],
        'anxious': ['worried', 'anxious', 'concerned']
    }

    emotion = "neutral"
    for e, words in emotion_map.items():
        if any(word in msg_lower for word in words):
            emotion = e
            break

    context_insights = {
        "romantic": "This appears to be a personal message that may involve feelings or relationship dynamics.",
        "coparenting": "This message likely relates to child-related matters or parenting coordination.",
        "workplace": "This seems to be a professional communication that may involve work tasks or relationships.",
        "family": "This appears to be a family-related message that may involve personal or domestic matters.",
        "friend": "This looks like a casual message between friends.",
        "general": "This is a general communication."
    }

    if is_received:
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "meaning": (f"📴 **Offline Analysis:** {context_insights.get(ctx, 'This is a general communication.')} "
                        f"The tone appears {sentiment} with {emotion} undertones. For detailed analysis, try again when API quota resets."),
            "need": "More context needed for detailed analysis",
            "response": (f"I understand you're sharing something important. Could you help me understand more about what you're looking "
                         f"for in this {ctx} situation?")
        }
    else:
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "reframed": (f"📴 **Offline Mode:** Here's a basic reframe - Consider saying: 'I'd like to discuss something regarding "
                         f"our {ctx} situation: {msg[:80]}{'...' if len(msg) > 80 else ''}'")
        }

def analyze(msg, ctx, is_received=False):
    current_usage, remaining, daily_limit = get_quota_info()
    if remaining <= 0:
        st.warning(f"⚠️ Daily quota reached ({current_usage}/{daily_limit}). Using offline mode.")
        return get_offline_analysis(msg, ctx, is_received)

    prompt = (f'Context: {ctx}. Analyze this received message: "{msg}" '
              'Return JSON with keys: sentiment, emotion, meaning, need, response') if is_received else (
              f'Context: {ctx}. Help reframe this message: "{msg}" '
              'Return JSON with keys: sentiment, emotion, reframed')

    ai_model = get_ai(st.session_state.api_key)
    for attempt in range(3):
        try:
            result = ai_model.generate_content(prompt)
            text = re.sub(r'``````', '', result.text)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            cleaned_text = json_match.group(0) if json_match else text
            parsed = json.loads(cleaned_text)

            required = ['sentiment', 'emotion', 'meaning', 'need', 'response'] if is_received else ['sentiment', 'emotion', 'reframed']
            missing_keys = [k for k in required if k not in parsed or not parsed[k]]
            if missing_keys:
                raise ValueError(f"Missing required keys: {missing_keys}")

            return parsed
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                st.error("🚫 **API Quota Exceeded**")
                st.info("**Solutions:** Wait (reset at midnight PST), Upgrade to paid plan, or Use offline mode")
                return get_offline_analysis(msg, ctx, is_received)
            if attempt == 2:
                return get_offline_analysis(msg, ctx, is_received)
            time.sleep(1)

def load_conversation(idx):
    entry = st.session_state.history[idx]
    st.session_state.active_msg = entry['original']
    st.session_state.active_ctx = entry['context']

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
            loaded_history = json.load(uploaded)
            if isinstance(loaded_history, list):
                st.session_state.history = loaded_history
                st.sidebar.success("✅ Loaded!")
            else:
                raise ValueError("Loaded file is not a list")
        except Exception:
            st.sidebar.error("❌ Invalid file format")

    if st.session_state.history:
        filename = f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
        st.sidebar.download_button("💾 Save", json.dumps(st.session_state.history, indent=2), filename)

        st.sidebar.markdown("📜 **This Session**")
        last_five = st.session_state.history[-5:]
        start_idx = len(st.session_state.history) - len(last_five)
        for i, entry in enumerate(last_five):
            real_idx = start_idx + i
            button_label = f"#{real_idx+1} {entry['context'][:3]} ({entry['time'][-5:]})"
            if st.sidebar.button(button_label, key=f"load_{real_idx}"):
                load_conversation(real_idx)
                st.experimental_rerun()

def render_context_selector(key_suffix=""):
    contexts = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
    idx = contexts.index(st.session_state.active_ctx) if st.session_state.active_ctx in contexts else 0
    return st.selectbox("Context:", contexts, index=idx, key=f"ctx{key_suffix}")

def render_analysis_tab(is_received=False):
    state = st.session_state
    tab_type = "Understand Message" if is_received else "Improve Message"
    st.markdown(f"### {tab_type}")

    msg_key = "translate_msg" if is_received else "coach_msg"
    msg = st.text_area("Received:" if is_received else "Message:", value=state.active_msg, height=120, key=msg_key)
    ctx = render_context_selector("2" if is_received else "")

    analyze_button_label = "🔍 Analyze" if is_received else "🚀 Analyze"
    if st.button(analyze_button_label, type="primary") and msg.strip():
        with st.spinner(f"Analyzing {'the received' if is_received else 'your'} message..."):
            state.count += 1
            result = analyze(msg, ctx, is_received)

            sentiment = result.get("sentiment", "neutral")
            emotion = result.get("emotion", "mixed")
            st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {emotion.title()}</div>', unsafe_allow_html=True)

            if is_received:
                meaning = result.get('meaning', 'Unable to analyze')
                box_class = "offline-box" if meaning.startswith("📴 **Offline Analysis:**") else "meaning-box"
                st.markdown(f'<div class="{box_class}"><strong>💭 What they mean:</strong><br>{meaning}</div>', unsafe_allow_html=True)

                need = result.get('need', 'Unable to determine')
                st.markdown(f'<div class="need-box"><strong>🎯 What they need:</strong><br>{need}</div>', unsafe_allow_html=True)

                response = result.get("response", "I understand.")
                st.markdown(f'<div class="ai-box"><strong>💬 Suggested response:</strong><br>{response}</div>', unsafe_allow_html=True)

                display_result = response
            else:
                improved = result.get("reframed", msg)
                st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)
                display_result = improved

            if st.button("📋 Copy", key=f"copy_btn_{'translate' if is_received else 'coach'}", help="Copy to clipboard"):
                st.success("✅ Copied to clipboard!")

            history_entry = {
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": "receive" if is_received else "send",
                "context": ctx,
                "original": msg,
                "result": display_result,
                "sentiment": sentiment,
            }

            if is_received:
                history_entry.update({"meaning": result.get('meaning', ''), "need": result.get('need', '')})

            state.history.append(history_entry)

# --- Main Script ---

defaults = {
    'token_validated': False,
    'api_key': st.secrets.get("GEMINI_API_KEY", ""),
    'count': 0,
    'history': [],
    'active_msg': '',
    'active_ctx': 'general'
}
init_sess_state_defaults(defaults)

# Token validation
if not st.session_state.token_validated:
    token = st.text_input("🔑 Beta Token:", type="password")
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
        st.session_state.token_validated = True
        st.success("✅ Welcome!")
        st.experimental_rerun()
    elif token:
        st.error("❌ Invalid token")
    if not st.session_state.token_validated:
        st.stop()

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

# API key input / validation
if not st.session_state.api_key:
    st.warning("⚠️ API Key Required")
    key = st.text_input("Gemini API Key:", type="password")
    if st.button("Save") and key:
        st.session_state.api_key = key
        st.success("✅ Saved!")
        st.experimental_rerun()
    st.stop()

# Sidebar rendering
render_quota_sidebar()
st.sidebar.markdown("---")
render_history_sidebar()

# Main content with tabs
tab1, tab2, tab3 = st.tabs(["📤 Coach", "📥 Translate", "ℹ️ About"])

with tab1:
    render_analysis_tab(is_received=False)

with tab2:
    render_analysis_tab(is_received=True)

with tab3:
    st.image("logo.png", width=200)
    st.markdown(
        """### The Third Voice
**AI communication coach** for better conversations.

**Features:**
- 📤 **Coach:** Improve outgoing messages
- 📥 **Translate:** Understand incoming messages with deep analysis

- 📜 **History:** Session tracking with save/load

**Contexts:** General, Romantic, Coparenting, Workplace, Family, Friend

**Privacy:** Local sessions only, manual save/load

*Beta v0.9.1 • Contact: hello@thethirdvoice.ai*"""
    )

st.markdown("---")
st.markdown("*Feedback: hello@thethirdvoice.ai*")
