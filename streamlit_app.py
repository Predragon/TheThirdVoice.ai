import streamlit as st
import google.generativeai as genai
import json
import datetime

# --- Constants ---
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]

# --- Session Init ---
for key, default in [
    ('token_validated', False),
    ('api_key', st.secrets.get("GEMINI_API_KEY", "")),
    ('count', 0),
    ('history', []),
    ('active_msg', ''),
    ('active_ctx', 'general')
]:
    if key not in st.session_state: st.session_state[key] = default

# --- Token Gate ---
if not st.session_state.token_validated:
    token = st.text_input("🔑 Beta Token:", type="password")
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
        st.session_state.token_validated = True
        st.success("✅ Welcome!")
        st.rerun()
    elif token:
        st.error("❌ Invalid token")
    st.stop()

# --- Page Setup ---
st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
.ai-box {background:#f0f8ff;padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0}
.pos{background:#d4edda;padding:0.5rem;border-radius:5px;color:#155724;margin:0.2rem 0}
.neg{background:#f8d7da;padding:0.5rem;border-radius:5px;color:#721c24;margin:0.2rem 0}
.neu{background:#d1ecf1;padding:0.5rem;border-radius:5px;color:#0c5460;margin:0.2rem 0}
.sidebar .element-container{margin-bottom:0.5rem}
</style>
""", unsafe_allow_html=True)

# --- Gemini AI Setup ---
@st.cache_resource
def get_ai():
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# --- AI Prompt Handler ---
def analyze(msg, ctx, is_received=False):
    prompts = {
        False: f'Context: {ctx}. Reframe message: "{msg}"\nJSON: {{"sentiment": "positive/negative/neutral", "emotion": "emotion", "reframed": "better version"}}',
        True: f'Context: {ctx}. Analyze: "{msg}"\nJSON: {{"sentiment": "positive/negative/neutral", "emotion": "emotion", "meaning": "what they mean", "need": "what they need", "response": "suggested response"}}'
    }
    try:
        return json.loads(get_ai().generate_content(prompts[is_received]).text)
    except Exception as e:
        st.error(f"⚠️ AI error: {e}")
        return {
            "sentiment": "neutral", "emotion": "mixed",
            "reframed": msg, "meaning": "Unknown", "need": "Understanding", "response": "I understand."
        }

# --- Sidebar Context & History ---
st.sidebar.markdown("### 🗂️ Conversation Category")
selected_context = st.sidebar.radio("Select context", CONTEXTS, index=CONTEXTS.index(st.session_state.active_ctx))
st.session_state.active_ctx = selected_context
st.sidebar.markdown("---")
st.sidebar.markdown("### 📜 Manage History")

# Load history (compact, no drag-drop)
uploaded = st.sidebar.file_uploader("📤 Load (.json)", type="json", label_visibility="collapsed")
if uploaded:
    try:
        st.session_state.history = json.load(uploaded)
        st.sidebar.success("✅ Loaded!")
    except:
        st.sidebar.error("❌ Invalid file")

# Save history (only if there's something to save)
if st.session_state.history:
    st.sidebar.download_button(
        "💾 Save (.json)",
        json.dumps(st.session_state.history, indent=2),
        file_name=f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json",
        use_container_width=True
    )

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📤 Coach", "📥 Translate", "📜 History", "ℹ️ About"])

# --- Coach Tab ---
with tab1:
    st.markdown("### ✍️ Improve Message")
    msg = st.text_area("Your message:", value=st.session_state.active_msg, height=80, key="coach_msg")

    if st.button("🚀 Improve", type="primary") and msg.strip():
        st.session_state.count += 1
        result = analyze(msg, st.session_state.active_ctx)
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
        improved = result.get("reframed", msg)
        st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)

        st.session_state.history.append({
            "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
            "type": "send",
            "context": st.session_state.active_ctx,
            "original": msg,
            "result": improved,
            "sentiment": sentiment
        })
        st.code(improved, language="text")

# --- Translate Tab ---
with tab2:
    st.markdown("### 🧠 Understand Received Message")
    msg = st.text_area("Received message:", value=st.session_state.active_msg, height=80, key="translate_msg")

    if st.button("🔍 Analyze", type="primary") and msg.strip():
        st.session_state.count += 1
        result = analyze(msg, st.session_state.active_ctx, True)
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
        st.markdown(f"**Meaning:** {result.get('meaning', '...')}")
        st.markdown(f"**Need:** {result.get('need', '...')}")
        st.markdown(f'<div class="ai-box">{result.get("response", "I understand.")}</div>', unsafe_allow_html=True)

        st.session_state.history.append({
            "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
            "type": "receive",
            "context": st.session_state.active_ctx,
            "original": msg,
            "result": result.get("response", msg),
            "sentiment": sentiment
        })
        st.code(result.get("response", msg), language="text")

# --- History Tab ---
with tab3:
    st.markdown("### 📜 Conversation History")
    filter_ctx = st.selectbox("Filter by context", CONTEXTS, index=CONTEXTS.index(st.session_state.active_ctx), key="history_filter")

    filtered = [h for h in st.session_state.history if h['context'] == filter_ctx]
    if not filtered:
        st.info("No messages yet for this context.")
    else:
        for i, entry in enumerate(reversed(filtered)):
            st.markdown(f"#### Message #{len(filtered) - i}")
            st.markdown(f"- 🕒 `{entry['time']}`")
            st.markdown(f"- 💬 **Type:** `{entry['type']}`")
            st.markdown(f"- 😊 **Sentiment:** `{entry['sentiment']}`")
            st.markdown(f"- ✉️ **Original:** {entry['original']}")
            st.markdown(f"<div class='ai-box'>{entry['result']}</div>", unsafe_allow_html=True)
            st.markdown("---")

# --- About Tab ---
with tab4:
    st.markdown("""### ℹ️ About The Third Voice
**AI communication coach** for better conversations.

**Core Features:**
- 📤 **Coach:** Improve outgoing messages
- 📥 **Translate:** Understand incoming messages  
- 📜 **History:** View & filter by conversation type

**Contexts Supported:**  
General • Romantic • Coparenting • Workplace • Family • Friend

🛡️ **Privacy:** Local only. No data is uploaded.  
🧪 *Beta v0.9.1* — Feedback: [hello@thethirdvoice.ai](mailto:hello@thethirdvoice.ai)
""")
