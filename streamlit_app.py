import streamlit as st
import json
import datetime

# --- Constants ---
CONTEXTS = [ "romantic", "coparenting", "workplace", "family", "friend"]

# --- Session Init ---
for key, default in [
    ('token_validated', True),  # bypassed token for mock testing
    ('api_key', ''),            # empty if mocking AI
    ('count', 0),
    ('history', []),
    ('active_msg', ''),
    ('active_ctx', 'general')
]:
    if key not in st.session_state: st.session_state[key] = default

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

# --- Mock AI Response ---
def mock_analyze(msg, ctx, is_received=False):
    if is_received:
        return {
            "sentiment": "neutral",
            "emotion": "confused",
            "meaning": f"Mock understanding of: {msg}",
            "need": "Clarity",
            "response": f"Thanks for sharing that. Let's talk more about it."
        }
    else:
        return {
            "sentiment": "neutral",
            "emotion": "calm",
            "reframed": f"I'd like to express: {msg}"
        }

# --- Sidebar: Context & History Controls ---
st.sidebar.markdown("### 🗂️ Conversation Category")
selected_context = st.sidebar.radio("Select context", CONTEXTS, index=CONTEXTS.index(st.session_state.active_ctx))
st.session_state.active_ctx = selected_context

st.sidebar.markdown("---")
st.sidebar.markdown("### 📜 Manage History")

# Load history
uploaded = st.sidebar.file_uploader("📤 Load (.json)", type="json", label_visibility="collapsed")
if uploaded:
    try:
        history_data = json.load(uploaded)
        if isinstance(history_data, list) and all('original' in h and 'result' in h for h in history_data):
            st.session_state.history = history_data
            st.sidebar.success("✅ History loaded!")
        else:
            st.sidebar.warning("⚠️ Format issue: loaded but may be incomplete")
    except json.JSONDecodeError:
        st.sidebar.error("❌ Not valid JSON")
    except Exception as e:
        st.sidebar.error(f"❌ Error loading: {e}")

# Save history
if st.session_state.history:
    st.sidebar.download_button(
        "💾 Save (.json)",
        json.dumps(st.session_state.history, indent=2),
        file_name=f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json",
        use_container_width=True
    )

# Clear history
if st.session_state.history:
    if st.sidebar.button("🧹 Clear History", use_container_width=True):
        st.session_state.history.clear()
        st.sidebar.info("History cleared.")

# Count messages per selected context
ctx_count = sum(1 for h in st.session_state.history if h['context'] == st.session_state.active_ctx)
st.sidebar.caption(f"🗒️ {ctx_count} messages in '{st.session_state.active_ctx}'")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📤 Coach", "📥 Translate", "📜 History", "ℹ️ About"])

# --- Tab 1: Coach ---
with tab1:
    st.markdown("### ✍️ Improve Message")
    msg = st.text_area("Your message:", value=st.session_state.active_msg, height=80, key="coach_msg")
    if st.button("🚀 Improve", type="primary"):
        st.session_state.count += 1
        result = mock_analyze(msg, st.session_state.active_ctx)
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "neutral").title()}</div>', unsafe_allow_html=True)
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

# --- Tab 2: Translate ---
with tab2:
    st.markdown("### 🧠 Understand Received Message")
    msg = st.text_area("Received message:", value=st.session_state.active_msg, height=80, key="translate_msg")
    if st.button("🔍 Analyze", type="primary"):
        st.session_state.count += 1
        result = mock_analyze(msg, st.session_state.active_ctx, True)
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "neutral").title()}</div>', unsafe_allow_html=True)
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

# --- Tab 3: History ---
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

# --- Tab 4: About ---
with tab4:
    st.markdown("""### ℹ️ About The Third Voice
**AI communication coach** for better conversations.

**Core Features:**
- 📤 **Coach:** Improve outgoing messages
- 📥 **Translate:** Understand incoming messages  
- 📜 **History:** View & filter by conversation type

**Supported Contexts:**  
General • Romantic • Coparenting • Workplace • Family • Friend

🛡️ **Privacy:** Local only. No data is uploaded.  
🧪 *Beta v0.9.2* — Feedback: [hello@thethirdvoice.ai](mailto:hello@thethirdvoice.ai)
""")
