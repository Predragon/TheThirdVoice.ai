import streamlit as st
import google.generativeai as genai
import json
import datetime

# Session state init
for key, default in [('token_validated', False), ('api_key', st.secrets.get("GEMINI_API_KEY", "")), ('count', 0), ('history', [])]:
    if key not in st.session_state: st.session_state[key] = default

# Token validation
if not st.session_state.token_validated:
    token = st.text_input("🔑 Beta Token:", type="password")
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]: st.session_state.token_validated = True; st.success("✅ Welcome!"); st.rerun()
    elif token: st.error("❌ Invalid token")
    if not st.session_state.token_validated: st.stop()

st.set_page_config(page_title="The Third Voice", page_icon="🎙️")
st.markdown("""<style>.ai-box{background:#f0f8ff;padding:1rem;border-radius:8px;border-left:4px solid #4CAF50}.pos{background:#d4edda;padding:0.5rem;border-radius:5px;color:#155724}.neg{background:#f8d7da;padding:0.5rem;border-radius:5px;color:#721c24}.neu{background:#d1ecf1;padding:0.5rem;border-radius:5px;color:#0c5460}</style>""", unsafe_allow_html=True)

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

def analyze(msg, ctx, recv=False):
    try:
        if recv:
            prompt = f'Context: {ctx}. Analyze received message, suggest response: "{msg}"\nReturn JSON: {{"sentiment": "positive/negative/neutral", "emotion": "main emotion", "meaning": "what they mean", "need": "what they need", "response": "suggested response"}}'
        else:
            prompt = f'Context: {ctx}. Analyze and reframe message: "{msg}"\nReturn JSON: {{"sentiment": "positive/negative/neutral", "emotion": "main emotion", "reframed": "better version"}}'
        return json.loads(get_ai().generate_content(prompt).text)
    except:
        if recv:
            return {"sentiment": "neutral", "emotion": "mixed", "meaning": "Processing...", "need": "Understanding", "response": "I understand."}
        else:
            return {"sentiment": "neutral", "emotion": "mixed", "reframed": f"I'd like to discuss: {msg}"}

st.markdown("# 🎙️ The Third Voice")
st.sidebar.markdown(f"**Uses:** {st.session_state.count}/1500")

tab1, tab2, tab3, tab4 = st.tabs(["📤 Coach", "📥 Translate", "📜 History", "ℹ️ About"])

with tab1:
    st.markdown("### Improve Message")
    msg = st.text_area("Message:", height=80)
    ctx = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace", "family", "friend"])
    if st.button("🚀 Analyze", type="primary") and msg.strip():
        st.session_state.count += 1
        result = analyze(msg, ctx)
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
        improved = result.get("reframed", msg)
        st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)
        st.session_state.history.append({"time": datetime.datetime.now().strftime("%m/%d %H:%M"), "type": "send", "context": ctx, "original": msg, "result": improved, "sentiment": sentiment})
        st.code(improved)

with tab2:
    st.markdown("### Understand Message")
    msg = st.text_area("Received:", height=80)
    ctx = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace", "family", "friend"], key="ctx2")
    if st.button("🔍 Analyze", type="primary") and msg.strip():
        st.session_state.count += 1
        result = analyze(msg, ctx, True)
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
        st.markdown(f"**Mean:** {result.get('meaning', 'Processing...')}")
        st.markdown(f"**Need:** {result.get('need', 'Understanding')}")
        response = result.get("response", "I understand.")
        st.markdown(f'<div class="ai-box">{response}</div>', unsafe_allow_html=True)
        st.session_state.history.append({"time": datetime.datetime.now().strftime("%m/%d %H:%M"), "type": "receive", "context": ctx, "original": msg, "result": response, "sentiment": sentiment})
        st.code(response)

with tab3:
    st.markdown("### History")
    if not st.session_state.history: st.info("No history yet")
    else:
        for entry in reversed(st.session_state.history[-10:]):
            icon = "📤" if entry["type"] == "send" else "📥"
            with st.expander(f"{icon} {entry['time']} - {entry['context']} ({entry['sentiment']})"):
                st.markdown(f"**Original:** {entry['original']}")
                st.markdown(f"**Result:** {entry['result']}")
        if st.button("💾 Download"): st.download_button("Save", json.dumps(st.session_state.history, indent=2), f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json")
        if st.button("🗑️ Clear") and st.button("Confirm"): st.session_state.history = []; st.rerun()

with tab4:
    st.markdown("""### About The Third Voice
**AI communication coach** that helps improve your messages and understand others better.

**Features:**
- 📤 **Coach:** Improve messages before sending
- 📥 **Translate:** Understand received messages
- 📜 **History:** Track your communication patterns

**Contexts:** General, Romantic, Coparenting, Workplace, Family, Friend

**Privacy:** Messages processed temporarily, not stored permanently

**Contact:** hello@thethirdvoice.ai

*Beta v0.9 • Built with ❤️ by Predrag*""")

st.markdown("---")
st.markdown("*The Third Voice Beta • Feedback: hello@thethirdvoice.ai*")
