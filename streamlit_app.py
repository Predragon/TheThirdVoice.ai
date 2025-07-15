import streamlit as st
import google.generativeai as genai
import json
import datetime
import re
import time

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

# Compact CSS with dark theme support
st.markdown("""<style>
.ai-box{background:#f0f8ff;padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0;color:#000;position:relative}
.pos{background:#d4edda;padding:0.5rem;border-radius:5px;color:#155724;margin:0.2rem 0;font-weight:bold}
.neg{background:#f8d7da;padding:0.5rem;border-radius:5px;color:#721c24;margin:0.2rem 0;font-weight:bold}
.neu{background:#d1ecf1;padding:0.5rem;border-radius:5px;color:#0c5460;margin:0.2rem 0;font-weight:bold}
.sidebar .element-container{margin-bottom:0.5rem}
.copy-btn{background:#4CAF50;color:white;border:none;padding:8px 16px;border-radius:5px;cursor:pointer;font-size:14px;font-weight:bold;margin-top:10px}
.copy-btn:hover{background:#45a049}
.meaning-box{background:#f8f9fa;padding:1rem;border-radius:8px;border-left:4px solid #17a2b8;margin:0.5rem 0;color:#000}
.need-box{background:#fff3cd;padding:1rem;border-radius:8px;border-left:4px solid #ffc107;margin:0.5rem 0;color:#000}
.error-box{background:#f8d7da;padding:1rem;border-radius:8px;border-left:4px solid #dc3545;margin:0.5rem 0;color:#721c24}
[data-theme="dark"] .ai-box{background:#1e3a5f;color:#fff;border-left-color:#4CAF50}
[data-theme="dark"] .pos{background:#2d5a3d;color:#90ee90}
[data-theme="dark"] .neg{background:#5a2d2d;color:#ffb3b3}
[data-theme="dark"] .neu{background:#2d4a5a;color:#87ceeb}
[data-theme="dark"] .copy-btn{background:#2d5a3d}
[data-theme="dark"] .meaning-box{background:#2d4a5a;color:#87ceeb;border-left-color:#17a2b8}
[data-theme="dark"] .need-box{background:#5a5a2d;color:#ffeb3b;border-left-color:#ffc107}
[data-theme="dark"] .error-box{background:#5a2d2d;color:#ffb3b3;border-left-color:#dc3545}
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

def clean_json_response(text):
    """Clean and extract JSON from AI response"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*|\s*```', '', text)
    # Find JSON-like content
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return text

def analyze(msg, ctx, is_received=False, retry_count=0):
    if is_received:
        prompt = f'''Context: {ctx}. Analyze this received message: "{msg}"

Please provide a detailed analysis in JSON format with these exact keys:
- "sentiment": "positive", "negative", or "neutral"
- "emotion": the main emotion detected
- "meaning": what the person is really trying to communicate (be specific and insightful)
- "need": what the person needs or wants from this communication
- "response": a suggested empathetic response

Return only valid JSON, no explanations.'''
    else:
        prompt = f'''Context: {ctx}. Help reframe this message: "{msg}"

Please provide a better version in JSON format with these exact keys:
- "sentiment": "positive", "negative", or "neutral"
- "emotion": the main emotion in the original message
- "reframed": a more effective version of the message

Return only valid JSON, no explanations.'''
    
    try:
        result = get_ai().generate_content(prompt)
        cleaned_text = clean_json_response(result.text)
        parsed_result = json.loads(cleaned_text)
        
        # Validate required keys
        if is_received:
            required_keys = ['sentiment', 'emotion', 'meaning', 'need', 'response']
        else:
            required_keys = ['sentiment', 'emotion', 'reframed']
        
        for key in required_keys:
            if key not in parsed_result or not parsed_result[key]:
                raise ValueError(f"Missing or empty key: {key}")
        
        return parsed_result
        
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        
        # Retry logic
        if retry_count < 2:
            time.sleep(1)
            return analyze(msg, ctx, is_received, retry_count + 1)
        
        # Fallback with more specific error handling
        if is_received:
            return {
                "sentiment": "neutral", 
                "emotion": "unclear", 
                "meaning": f"Unable to fully analyze this message. It appears to be a {ctx} communication that may need further context to interpret properly.",
                "need": "Clarification or more context may be helpful",
                "response": "I'd like to better understand what you're trying to communicate. Could you help me understand your perspective?"
            }
        else:
            return {
                "sentiment": "neutral", 
                "emotion": "mixed", 
                "reframed": f"I'd like to discuss something important regarding {ctx}: {msg[:100]}{'...' if len(msg) > 100 else ''}"
            }

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
st.image("logo.png", width=200)
tab1, tab2, tab3 = st.tabs(["📤 Coach", "📥 Translate", "ℹ️ About"])

with tab1:
    st.markdown("### Improve Message")
    msg = st.text_area("Message:", value=st.session_state.active_msg, height=120, key="coach_msg")
    ctx = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace", "family", "friend"], 
                      index=["general", "romantic", "coparenting", "workplace", "family", "friend"].index(st.session_state.active_ctx))
    
    if st.button("🚀 Analyze", type="primary") and msg.strip():
        with st.spinner("Analyzing your message..."):
            st.session_state.count += 1
            result = analyze(msg, ctx)
            sentiment = result.get("sentiment", "neutral")
            
            st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
            improved = result.get("reframed", msg)
            
            # AI output box with copy functionality
            st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)
            if st.button("📋 Copy Message", key="copy_btn_coach", help="Copy improved message"):
                st.success("✅ Copied to clipboard!")
            
            st.session_state.history.append({
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": "send",
                "context": ctx,
                "original": msg,
                "result": improved,
                "sentiment": sentiment
            })

with tab2:
    st.markdown("### Understand Message")
    msg = st.text_area("Received:", value=st.session_state.active_msg, height=120, key="translate_msg")
    ctx = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace", "family", "friend"], 
                      index=["general", "romantic", "coparenting", "workplace", "family", "friend"].index(st.session_state.active_ctx), key="ctx2")
    
    if st.button("🔍 Analyze", type="primary") and msg.strip():
        with st.spinner("Analyzing the received message..."):
            st.session_state.count += 1
            result = analyze(msg, ctx, True)
            sentiment = result.get("sentiment", "neutral")
            
            # Sentiment and emotion display
            st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
            
            # Enhanced meaning display
            meaning = result.get('meaning', 'Unable to analyze')
            if meaning != "Processing...":
                st.markdown(f'<div class="meaning-box"><strong>💭 What they mean:</strong><br>{meaning}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box"><strong>⚠️ Analysis incomplete:</strong><br>The message analysis is still processing. Please try again.</div>', unsafe_allow_html=True)
            
            # Enhanced need display
            need = result.get('need', 'Unable to determine')
            st.markdown(f'<div class="need-box"><strong>🎯 What they need:</strong><br>{need}</div>', unsafe_allow_html=True)
            
            # Suggested response
            response = result.get("response", "I understand.")
            st.markdown(f'<div class="ai-box"><strong>💬 Suggested response:</strong><br>{response}</div>', unsafe_allow_html=True)
            
            if st.button("📋 Copy Response", key="copy_btn_translate", help="Copy suggested response"):
                st.success("✅ Copied to clipboard!")
            
            st.session_state.history.append({
                "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                "type": "receive",
                "context": ctx,
                "original": msg,
                "result": response,
                "sentiment": sentiment,
                "meaning": meaning,
                "need": need
            })

with tab3:
    st.markdown("""### The Third Voice
**AI communication coach** for better conversations.

**Features:**
- 📤 **Coach:** Improve outgoing messages
- 📥 **Translate:** Understand incoming messages with deep analysis
- 📜 **History:** Session tracking with save/load

**Contexts:** General, Romantic, Coparenting, Workplace, Family, Friend

**Enhanced Tab 2 Features:**
- Better error handling and retry logic
- More detailed meaning analysis
- Clearer need identification
- Improved response suggestions
- Visual separation of analysis components

**Privacy:** Local sessions only, manual save/load

*Beta v0.9.1 • Contact: hello@thethirdvoice.ai*""")

st.markdown("---")
st.markdown("*Feedback: hello@thethirdvoice.ai*")
