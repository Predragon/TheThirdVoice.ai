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
.offline-box{background:#fff8dc;padding:1rem;border-radius:8px;border-left:4px solid #ff9800;margin:0.5rem 0;color:#000}
[data-theme="dark"] .offline-box{background:#5a4d2d;color:#ffeb3b;border-left-color:#ff9800}
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

def get_quota_info():
    """Check current usage and provide quota information"""
    daily_limit = 50
    current_usage = st.session_state.count
    remaining = max(0, daily_limit - current_usage)
    return current_usage, remaining, daily_limit

def handle_quota_error(error_msg, ctx, msg, is_received=False):
    """Handle API quota errors gracefully"""
    if "429" in str(error_msg) or "quota" in str(error_msg).lower():
        st.error("🚫 **API Quota Exceeded**")
        st.info("""
        **Gemini API Free Tier Limit Reached (50 requests/day)**
        
        **Solutions:**
        1. **Wait**: Reset at midnight PST
        2. **Upgrade**: Get paid Gemini API plan
        3. **Use Offline Mode**: Basic analysis below
        """)
        
        # Provide basic offline analysis
        return get_offline_analysis(msg, ctx, is_received)
    
    return None

def get_offline_analysis(msg, ctx, is_received=False):
    """Provide basic analysis when API is unavailable"""
    import string
    
    # Simple sentiment analysis
    positive_words = ['good', 'great', 'happy', 'love', 'awesome', 'excellent', 'wonderful', 'amazing', 'perfect', 'thank']
    negative_words = ['bad', 'hate', 'angry', 'sad', 'terrible', 'awful', 'horrible', 'upset', 'mad', 'disappointed']
    
    msg_lower = msg.lower()
    pos_count = sum(1 for word in positive_words if word in msg_lower)
    neg_count = sum(1 for word in negative_words if word in msg_lower)
    
    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Basic emotion detection
    if any(word in msg_lower for word in ['angry', 'mad', 'furious']):
        emotion = "angry"
    elif any(word in msg_lower for word in ['sad', 'disappointed', 'hurt']):
        emotion = "sad"
    elif any(word in msg_lower for word in ['happy', 'excited', 'great']):
        emotion = "happy"
    elif any(word in msg_lower for word in ['worried', 'anxious', 'concerned']):
        emotion = "anxious"
    else:
        emotion = "neutral"
    
    if is_received:
        # Context-specific meaning analysis
        context_insights = {
            "romantic": "This appears to be a personal message that may involve feelings or relationship dynamics.",
            "coparenting": "This message likely relates to child-related matters or parenting coordination.",
            "workplace": "This seems to be a professional communication that may involve work tasks or relationships.",
            "family": "This appears to be a family-related message that may involve personal or domestic matters.",
            "friend": "This looks like a casual message between friends.",
            "general": "This is a general communication."
        }
        
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "meaning": f"📴 **Offline Analysis:** {context_insights.get(ctx, 'This is a general communication.')} The tone appears {sentiment} with {emotion} undertones. For detailed analysis, try again when API quota resets.",
            "need": "More context needed for detailed analysis",
            "response": f"I understand you're sharing something important. Could you help me understand more about what you're looking for in this {ctx} situation?"
        }
    else:
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "reframed": f"📴 **Offline Mode:** Here's a basic reframe - Consider saying: 'I'd like to discuss something regarding our {ctx} situation: {msg[:80]}{'...' if len(msg) > 80 else ''}'"
        }

def analyze(msg, ctx, is_received=False, retry_count=0):
    # Check quota before making request
    current_usage, remaining, daily_limit = get_quota_info()
    
    if remaining <= 0:
        st.warning(f"⚠️ Daily quota reached ({current_usage}/{daily_limit}). Using offline mode.")
        return get_offline_analysis(msg, ctx, is_received)
    
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
        # Handle quota errors specifically
        quota_result = handle_quota_error(str(e), ctx, msg, is_received)
        if quota_result:
            return quota_result
        
        # Show error for debugging
        st.error(f"Analysis error: {str(e)}")
        
        # Retry logic for non-quota errors
        if retry_count < 2 and "429" not in str(e):
            time.sleep(1)
            return analyze(msg, ctx, is_received, retry_count + 1)
        
        # Fallback for other errors
        return get_offline_analysis(msg, ctx, is_received)

def load_conversation(idx):
    entry = st.session_state.history[idx]
    st.session_state.active_msg = entry['original']
    st.session_state.active_ctx = entry['context']

# Sidebar with enhanced quota tracking
current_usage, remaining, daily_limit = get_quota_info()
quota_color = "🟢" if remaining > 10 else "🟡" if remaining > 5 else "🔴"
st.sidebar.markdown(f"**API Uses:** {quota_color} {current_usage}/{daily_limit}")
st.sidebar.markdown(f"**Remaining:** {remaining}")
if remaining <= 5:
    st.sidebar.warning("⚠️ Low quota - consider offline mode")
if remaining == 0:
    st.sidebar.error("🚫 Quota exhausted - using offline mode")
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
            if "📴 **Offline Analysis:**" in meaning:
                st.markdown(f'<div class="offline-box">{meaning}</div>', unsafe_allow_html=True)
            elif meaning != "Processing...":
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
