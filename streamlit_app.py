import streamlit as st
import google.generativeai as genai
import json
import datetime

# Compact session state init
for key, default in [('token_validated', False), ('api_key', st.secrets.get("GEMINI_API_KEY", "")), ('count', 0), ('history', []), ('active_msg', ''), ('active_ctx', 'general')]:
    if key not in st.session_state: st.session_state[key] = default

# Token validation
if not st.session_state.token_validated:
    token = st.text_input("🔑 Beta Token:", type="password")
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]: st.session_state.token_validated = True; st.success("✅ Welcome!"); st.rerun()
    elif token: st.error("❌ Invalid token")
    if not st.session_state.token_validated: st.stop()

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")

# Compact CSS
st.markdown("""<style>
.ai-box{background:#f0f8ff;padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0}
.pos{background:#d4edda;padding:0.5rem;border-radius:5px;color:#155724;margin:0.2rem 0}
.neg{background:#f8d7da;padding:0.5rem;border-radius:5px;color:#721c24;margin:0.2rem 0}
.neu{background:#d1ecf1;padding:0.5rem;border-radius:5px;color:#0c5460;margin:0.2rem 0}
.sidebar .element-container{margin-bottom:0.5rem}
</style>""", unsafe_allow_html=True)

# API setup
if not st.session_state.api_key:
    st.warning("⚠️ API Key Required")
    key = st.text_input("Gemini API Key:", type="password")
    if st.button("Save") and key: st.session_state.api_key = key; st.success("✅ Saved!"); st.rerun()
    st.stop()

@st.cache_resource
def get_ai():
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def analyze(msg, ctx, is_received=False):
    prompts = {
        False: f'Context: {ctx}. Reframe message: "{msg}"\nJSON: {{"sentiment": "positive/negative/neutral", "emotion": "emotion", "reframed": "better version"}}',
        True: f'Context: {ctx}. Analyze: "{msg}"\nJSON: {{"sentiment": "positive/negative/neutral", "emotion": "emotion", "meaning": "what they mean", "need": "what they need", "response": "suggested response"}}'
    }
    try:
        return json.loads(get_ai().generate_content(prompts[is_received]).text)
    except:
        return {"sentiment": "neutral", "emotion": "mixed", "reframed": f"I'd like to discuss: {msg}", "meaning": "Processing...", "need": "Understanding", "response": "I understand."}

def load_conversation(idx):
    entry = st.session_state.history[idx]
    st.session_state.active_msg = entry['original']
    st.session_state.active_ctx = entry['context']

# Sidebar
st.sidebar.markdown(f"**Uses:** {st.session_state.count}/1500")
st.sidebar.markdown("---")

# Upload/Download in sidebar
uploaded = st.sidebar.file_uploader("📤 Load History", type="json")
if uploaded:
    try:
        st.session_state.history = json.load(uploaded)
        st.sidebar.success("✅ Loaded!")
    except:
        st.sidebar.error("❌ Invalid file")

if st.session_state.history:
    st.sidebar.download_button("💾 Save", json.dumps(st.session_state.history, indent=2), f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json")

# Session history in sidebar
if st.session_state.history:
    st.sidebar.markdown("📜 **This Session**")
    for i, entry in enumerate(st.session_state.history[-5:]):
        real_idx = len(st.session_state.history) - 5 + i
        if st.sidebar.button(f"#{real_idx+1} {entry['context'][:3]} ({entry['time'][-5:]})", key=f"load_{real_idx}"):
            load_conversation(real_idx)
            st.rerun()

# Main content
st.markdown("# 🎙️ The Third Voice")
tab1, tab2, tab3 = st.tabs(["📤 Coach", "📥 Translate", "ℹ️ About"])

with tab1:
    st.markdown("### Improve Message")
    msg = st.text_area("Message:", value=st.session_state.active_msg, height=80, key="coach_msg")
    ctx = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace", "family", "friend"], 
                      index=["general", "romantic", "coparenting", "workplace", "family", "friend"].index(st.session_state.active_ctx))
    
    if st.button("🚀 Analyze", type="primary") and msg.strip():
        st.session_state.count += 1
        result = analyze(msg, ctx)
        sentiment = result.get("sentiment", "neutral")
        
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
        improved = result.get("reframed", msg)
        st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)
        
        st.session_state.history.append({
            "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
            "type": "send",
            "context": ctx,
            "original": msg,
            "result": improved,
            "sentiment": sentiment
        })
        st.code(improved, language="text")

with tab2:
    st.markdown("### Understand Message")
    msg = st.text_area("Received:", value=st.session_state.active_msg, height=80, key="translate_msg")
    ctx = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace", "family", "friend"], 
                      index=["general", "romantic", "coparenting", "workplace", "family", "friend"].index(st.session_state.active_ctx), key="ctx2")
    
    if st.button("🔍 Analyze", type="primary") and msg.strip():
        st.session_state.count += 1
        result = analyze(msg, ctx, True)
        sentiment = result.get("sentiment", "neutral")
        
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
        st.markdown(f"**Meaning:** {result.get('meaning', 'Processing...')}")
        st.markdown(f"**Need:** {result.get('need', 'Understanding')}")
        
        response = result.get("response", "I understand.")
        st.markdown(f'<div class="ai-box">{response}</div>', unsafe_allow_html=True)
        
        st.session_state.history.append({
            "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
            "type": "receive",
            "context": ctx,
            "original": msg,
            "result": response,
            "sentiment": sentiment
        })
        st.code(response, language="text")

with tab3:
    st.markdown("""### The Third Voice
**AI communication coach** for better conversations.

**Features:**
- 📤 **Coach:** Improve outgoing messages
- 📥 **Translate:** Understand incoming messages  
- 📜 **History:** Session tracking with save/load

**Contexts:** General, Romantic, Coparenting, Workplace, Family, Friend

**Privacy:** Local sessions only, manual save/load

*Beta v0.9 • Contact: hello@thethirdvoice.ai*""")

st.markdown("---")
st.markdown("*Feedback: hello@thethirdvoice.ai*")
