import streamlit as st
import google.generativeai as genai
import json
import datetime
import re
import time
from typing import Dict, Optional, Any
from functools import lru_cache

# Optimized session state initialization
DEFAULTS = {
    'token_validated': False, 
    'api_key': st.secrets.get("GEMINI_API_KEY", ""), 
    'count': 0, 
    'history': [], 
    'active_msg': '', 
    'active_ctx': 'general',
    'theme': 'light',
    'quota_cache': None,
    'quota_cache_time': 0
}

# Initialize session state only once
if 'initialized' not in st.session_state:
    st.session_state.update(DEFAULTS)
    st.session_state.initialized = True

# Optimized token validation
def validate_token():
    """Streamlined token validation"""
    if st.session_state.token_validated:
        return
    
    st.markdown("### 🔐 Beta Access Required")
    token = st.text_input("Enter your beta token:", type="password", 
                         help="Contact hello@thethirdvoice.ai for access")
    
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]: 
        st.session_state.token_validated = True
        st.success("✅ Welcome to The Third Voice!")
        st.rerun()
    elif token: 
        st.error("❌ Invalid token. Please check your token or contact support.")
        st.info("💡 Need a beta token? Email hello@thethirdvoice.ai")
    
    if not st.session_state.token_validated: 
        st.stop()

validate_token()

# Page config moved after validation for efficiency
st.set_page_config(
    page_title="The Third Voice", 
    page_icon="🎙️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Optimized CSS with variables and consolidated rules
@st.cache_data
def get_css():
    return """<style>
:root {
    --primary-blue: #4CAF50;
    --success-green: #28a745;
    --warning-yellow: #ffc107;
    --error-red: #dc3545;
    --info-blue: #17a2b8;
    --shadow: 0 2px 4px rgba(0,0,0,0.1);
    --border-radius: 10px;
    --small-radius: 6px;
}

.ai-box, .meaning-box, .need-box, .error-box, .offline-box {
    padding: 1.2rem;
    border-radius: var(--border-radius);
    margin: 0.8rem 0;
    color: #000;
    box-shadow: var(--shadow);
}

.ai-box { background: #f0f8ff; border-left: 4px solid var(--primary-blue); }
.meaning-box { background: #f8f9fa; border-left: 4px solid var(--info-blue); }
.need-box { background: #fff3cd; border-left: 4px solid var(--warning-yellow); }
.error-box { background: #f8d7da; border-left: 4px solid var(--error-red); color: #721c24; }
.offline-box { background: #fff8dc; border-left: 4px solid #ff9800; }

.pos, .neg, .neu { 
    padding: 0.6rem; 
    border-radius: var(--small-radius); 
    margin: 0.3rem 0; 
    font-weight: bold; 
}
.pos { background: #d4edda; color: #155724; border-left: 3px solid var(--success-green); }
.neg { background: #f8d7da; color: #721c24; border-left: 3px solid var(--error-red); }
.neu { background: #d1ecf1; color: #0c5460; border-left: 3px solid var(--info-blue); }

.quota-warning, .quota-error { 
    padding: 0.8rem; 
    border-radius: var(--small-radius); 
    margin: 0.5rem 0; 
}
.quota-warning { background: #fff3cd; color: #856404; border-left: 3px solid var(--warning-yellow); }
.quota-error { background: #f8d7da; color: #721c24; border-left: 3px solid var(--error-red); }

[data-theme="dark"] .ai-box { background: #1e3a5f; color: #fff; }
[data-theme="dark"] .pos { background: #2d5a3d; color: #90ee90; }
[data-theme="dark"] .neg { background: #5a2d2d; color: #ffb3b3; }
[data-theme="dark"] .neu { background: #2d4a5a; color: #87ceeb; }
[data-theme="dark"] .meaning-box { background: #2d4a5a; color: #87ceeb; }
[data-theme="dark"] .need-box { background: #5a5a2d; color: #ffeb3b; }
[data-theme="dark"] .offline-box { background: #5a4d2d; color: #ffeb3b; }

.stTabs [data-baseweb="tab-list"] { gap: 0; width: 100%; justify-content: stretch; }
.stTabs [data-baseweb="tab"] { flex: 1; text-align: center; padding: 12px; }
.stTabs [data-baseweb="tab-panel"] { padding: 20px; min-height: 70vh; }

.copy-success { background: #d4edda; color: #155724; padding: 0.5rem; border-radius: 5px; margin-top: 0.5rem; }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
.loading { animation: pulse 2s infinite; }
</style>"""

st.markdown(get_css(), unsafe_allow_html=True)

# Optimized API setup
def setup_api():
    """Streamlined API setup"""
    if st.session_state.api_key:
        return
    
    st.warning("⚠️ Gemini API Key Required")
    st.info("Get your free API key at: https://makersuite.google.com/app/apikey")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        key = st.text_input("Gemini API Key:", type="password", 
                           help="Your API key is stored securely in this session only")
    with col2:
        if st.button("💾 Save", type="primary") and key: 
            st.session_state.api_key = key
            st.success("✅ API Key saved!")
            st.rerun()
    
    if not key:
        st.stop()

setup_api()

# Cached AI model initialization
@st.cache_resource
def get_ai():
    """Initialize Gemini AI with caching"""
    try:
        genai.configure(api_key=st.session_state.api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"❌ API initialization failed: {str(e)}")
        return None

# Optimized quota management with caching
class QuotaManager:
    DAILY_LIMIT = 1500
    WARNING_THRESHOLD = 300
    CRITICAL_THRESHOLD = 100
    CACHE_DURATION = 30  # seconds
    
    @staticmethod
    def get_quota_info():
        """Get quota info with caching"""
        now = time.time()
        if (st.session_state.quota_cache and 
            now - st.session_state.quota_cache_time < QuotaManager.CACHE_DURATION):
            return st.session_state.quota_cache
        
        current_usage = st.session_state.count
        remaining = max(0, QuotaManager.DAILY_LIMIT - current_usage)
        result = (current_usage, remaining, QuotaManager.DAILY_LIMIT)
        
        st.session_state.quota_cache = result
        st.session_state.quota_cache_time = now
        return result
    
    @staticmethod
    def get_quota_status():
        """Get quota status efficiently"""
        _, remaining, _ = QuotaManager.get_quota_info()
        if remaining <= 0:
            return "critical", "🚫"
        elif remaining <= QuotaManager.CRITICAL_THRESHOLD:
            return "error", "🔴"
        elif remaining <= QuotaManager.WARNING_THRESHOLD:
            return "warning", "🟡"
        return "good", "🟢"
    
    @staticmethod
    def update_usage():
        """Update usage and clear cache"""
        st.session_state.count += 1
        st.session_state.quota_cache = None

# Optimized JSON cleaning with compiled regex
JSON_PATTERNS = [
    re.compile(r'```json\s*|\s*```'),
    re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL),
    re.compile(r'\{.*?\}', re.DOTALL)
]

def clean_json_response(text: str) -> str:
    """Optimized JSON cleaning"""
    text = JSON_PATTERNS[0].sub('', text)
    
    for pattern in JSON_PATTERNS[1:]:
        match = pattern.search(text)
        if match:
            return match.group(0)
    
    return text

# Optimized keyword sets with precompiled patterns
EMOTION_KEYWORDS = {
    'positive': set(['good', 'great', 'happy', 'love', 'awesome', 'excellent', 'wonderful', 
                    'amazing', 'perfect', 'thank', 'appreciate', 'glad', 'excited', 'fantastic']),
    'negative': set(['bad', 'hate', 'angry', 'sad', 'terrible', 'awful', 'horrible', 'upset', 
                    'mad', 'disappointed', 'frustrated', 'annoyed', 'worried', 'stressed']),
    'neutral': set(['okay', 'fine', 'alright', 'normal', 'usual', 'standard'])
}

EMOTION_MAP = {
    'angry': ['angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed'],
    'sad': ['sad', 'disappointed', 'hurt', 'depressed', 'down', 'blue'],
    'happy': ['happy', 'excited', 'great', 'joy', 'thrilled', 'elated'],
    'anxious': ['worried', 'anxious', 'concerned', 'nervous', 'stressed', 'tense'],
    'confused': ['confused', 'unclear', 'puzzled', 'lost', 'uncertain'],
    'grateful': ['thank', 'appreciate', 'grateful', 'thankful']
}

CONTEXT_INSIGHTS = {
    "romantic": "This appears to be a personal message involving romantic feelings or relationship dynamics.",
    "coparenting": "This message relates to child-related matters or parenting coordination between separated parents.",
    "workplace": "This is a professional communication that may involve work tasks, colleagues, or business matters.",
    "family": "This appears to be a family-related message involving personal or domestic family matters.",
    "friend": "This looks like a casual message between friends with informal tone.",
    "general": "This is a general communication without specific context."
}

@lru_cache(maxsize=100)
def get_sentiment_score(msg_lower: str):
    """Cached sentiment analysis"""
    pos_score = sum(1 for word in EMOTION_KEYWORDS['positive'] if word in msg_lower)
    neg_score = sum(1 for word in EMOTION_KEYWORDS['negative'] if word in msg_lower)
    neu_score = sum(1 for word in EMOTION_KEYWORDS['neutral'] if word in msg_lower)
    
    if pos_score > neg_score and pos_score > neu_score:
        return "positive"
    elif neg_score > pos_score and neg_score > neu_score:
        return "negative"
    return "neutral"

def get_enhanced_offline_analysis(msg: str, ctx: str, is_received: bool = False) -> Dict[str, Any]:
    """Optimized offline analysis"""
    msg_lower = msg.lower()
    sentiment = get_sentiment_score(msg_lower)
    
    # Find emotion efficiently
    emotion = "neutral"
    for e, words in EMOTION_MAP.items():
        if any(word in msg_lower for word in words):
            emotion = e
            break
    
    context_insight = CONTEXT_INSIGHTS.get(ctx, CONTEXT_INSIGHTS["general"])
    
    if is_received:
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "meaning": f"📴 **Offline Analysis:** {context_insight} The overall tone appears {sentiment} with {emotion} undertones. For detailed psychological analysis and nuanced interpretation, please try again when API quota resets at midnight PST.",
            "need": f"Based on the {sentiment} tone and {emotion} emotion, the sender likely needs acknowledgment and appropriate response. For specific needs analysis, API access is required.",
            "response": f"I understand you're sharing something important about this {ctx} situation. Thank you for letting me know. Could you help me understand what kind of response would be most helpful right now?"
        }
    else:
        msg_preview = msg[:100] + ('...' if len(msg) > 100 else '')
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "reframed": f"📴 **Offline Mode:** Here's a basic reframe - Consider this approach: 'I'd like to discuss something regarding our {ctx} situation. {msg_preview}' (For advanced reframing with tone optimization, API access is required)"
        }

def analyze_message(msg: str, ctx: str, is_received: bool = False, retry_count: int = 0) -> Dict[str, Any]:
    """Optimized message analysis"""
    current_usage, remaining, daily_limit = QuotaManager.get_quota_info()
    
    if remaining <= 0:
        st.warning(f"⚠️ Daily quota reached ({current_usage}/{daily_limit}). Using enhanced offline mode.")
        return get_enhanced_offline_analysis(msg, ctx, is_received)
    
    # Optimized prompt generation
    base_context = f"Communication context: {ctx}. Message length: {len(msg)} characters."
    
    if is_received:
        prompt = f'''{base_context}
        
Analyze this received message with deep psychological insight: "{msg}"

Provide a comprehensive analysis in JSON format with these exact keys:
- sentiment: "positive", "negative", or "neutral"
- emotion: primary emotion detected (angry, sad, happy, anxious, confused, grateful, etc.)
- meaning: detailed interpretation of what the sender really means, including subtext and emotional undertones
- need: what the sender needs from you based on their message (support, acknowledgment, action, etc.)
- response: a thoughtful, context-appropriate response that addresses their needs

Focus on emotional intelligence and communication psychology.'''
    else:
        prompt = f'''{base_context}

Help reframe this outgoing message to be more effective: "{msg}"

Provide improvement suggestions in JSON format with these exact keys:
- sentiment: current sentiment of the message
- emotion: primary emotion being expressed
- reframed: an improved version that is clearer, more empathetic, and more likely to achieve positive outcomes

Focus on clarity, empathy, and effectiveness for the {ctx} context.'''
    
    ai_model = get_ai()
    if not ai_model:
        return get_enhanced_offline_analysis(msg, ctx, is_received)
    
    try:
        result = ai_model.generate_content(prompt)
        
        if not result or not result.text:
            raise ValueError("Empty response from AI")
        
        cleaned_text = clean_json_response(result.text)
        parsed_result = json.loads(cleaned_text)
        
        # Validate required keys
        required_keys = (['sentiment', 'emotion', 'meaning', 'need', 'response'] 
                        if is_received else ['sentiment', 'emotion', 'reframed'])
        
        for key in required_keys:
            if key not in parsed_result or not parsed_result[key]:
                raise ValueError(f"Missing or empty key: {key}")
        
        # Update quota efficiently
        QuotaManager.update_usage()
        return parsed_result
        
    except json.JSONDecodeError:
        if retry_count < 2:
            time.sleep(0.5)  # Reduced wait time
            return analyze_message(msg, ctx, is_received, retry_count + 1)
        return get_enhanced_offline_analysis(msg, ctx, is_received)
        
    except Exception as e:
        # Handle quota errors efficiently
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["429", "quota", "rate limit"]):
            st.error("🚫 **API Quota Exceeded**")
            st.info("**Solutions:** Wait for reset (midnight PST) • Upgrade to paid plan • Use enhanced offline mode")
            return get_enhanced_offline_analysis(msg, ctx, is_received)
        
        if retry_count < 2:
            time.sleep(0.5)
            return analyze_message(msg, ctx, is_received, retry_count + 1)
        
        return get_enhanced_offline_analysis(msg, ctx, is_received)

def load_conversation(idx: int):
    """Optimized conversation loading"""
    if 0 <= idx < len(st.session_state.history):
        entry = st.session_state.history[idx]
        st.session_state.active_msg = entry['original']
        st.session_state.active_ctx = entry['context']

def render_quota_sidebar():
    """Optimized quota display"""
    current_usage, remaining, daily_limit = QuotaManager.get_quota_info()
    status, emoji = QuotaManager.get_quota_status()
    
    st.sidebar.markdown(f"### 📊 API Usage")
    st.sidebar.markdown(f"**Status:** {emoji} {status.title()}")
    st.sidebar.markdown(f"**Used:** {current_usage}/{daily_limit}")
    st.sidebar.markdown(f"**Remaining:** {remaining}")
    
    # Efficient progress calculation
    progress = min(current_usage / daily_limit, 1.0) if daily_limit > 0 else 0
    st.sidebar.progress(progress)
    
    # Status messages
    if status == "warning":
        st.sidebar.warning("⚠️ Approaching quota limit")
    elif status == "error":
        st.sidebar.error("🔴 Low quota remaining")
    elif status == "critical":
        st.sidebar.error("🚫 Quota exhausted - offline mode active")
    
    st.sidebar.markdown("*Resets daily at midnight PST*")

def render_history_sidebar():
    """Optimized history management"""
    st.sidebar.markdown("### 📁 History")
    
    # File operations
    col1, col2 = st.sidebar.columns(2)
    with col1:
        uploaded = st.file_uploader("📤 Load", type="json", key="history_upload")
    
    if uploaded:
        try:
            loaded_history = json.load(uploaded)
            if isinstance(loaded_history, list):
                st.session_state.history = loaded_history
                st.sidebar.success("✅ History loaded!")
            else:
                st.sidebar.error("❌ Invalid format")
        except Exception as e:
            st.sidebar.error(f"❌ Load error: {str(e)[:50]}")

    with col2:
        if st.session_state.history:
            # Efficient JSON serialization
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
            st.download_button(
                "💾 Save", 
                json.dumps(st.session_state.history, indent=2), 
                f"ttv_history_{timestamp}.json",
                "application/json"
            )
    
    # Optimized history display
    if st.session_state.history:
        history_len = len(st.session_state.history)
        st.sidebar.markdown(f"**This Session** ({history_len} entries)")
        
        # Show recent entries efficiently
        recent_entries = st.session_state.history[-10:]
        sentiment_emojis = {"positive": "😊", "negative": "😞", "neutral": "😐"}
        
        for i, entry in enumerate(recent_entries):
            real_idx = history_len - len(recent_entries) + i
            
            # Optimized display text generation
            entry_type = "📥" if entry['type'] == 'receive' else "📤"
            context_short = entry['context'][:8]
            time_short = entry['time'][-5:]
            sentiment_emoji = sentiment_emojis.get(entry['sentiment'], "🤔")
            
            display_text = f"{entry_type} {context_short} {time_short} {sentiment_emoji}"
            
            if st.sidebar.button(
                display_text, 
                key=f"load_{real_idx}",
                help=f"Load: {entry['original'][:50]}..."
            ):
                load_conversation(real_idx)
                st.rerun()
        
        # Clear history
        if st.sidebar.button("🗑️ Clear History", help="Clear all history"):
            st.session_state.history = []
            st.rerun()

# Optimized context data
CONTEXTS = {
    "general": "General communication",
    "romantic": "Romantic relationship",
    "coparenting": "Co-parenting coordination", 
    "workplace": "Professional/work",
    "family": "Family communication",
    "friend": "Friend conversation"
}

def render_context_selector(key_suffix: str = "") -> str:
    """Optimized context selector"""
    context_keys = list(CONTEXTS.keys())
    context_labels = [f"{key.title()} - {desc}" for key, desc in CONTEXTS.items()]
    
    try:
        current_idx = context_keys.index(st.session_state.active_ctx)
    except ValueError:
        current_idx = 0
    
    selected_idx = st.selectbox(
        "Context:", 
        range(len(context_keys)),
        format_func=lambda i: context_labels[i],
        index=current_idx, 
        key=f"ctx{key_suffix}",
        help="Choose the communication context for better analysis"
    )
    
    return context_keys[selected_idx]

def render_analysis_tab(is_received: bool = False):
    """Optimized analysis tab"""
    tab_type = "Understand Message" if is_received else "Improve Message"
    icon = "📥" if is_received else "📤"
    
    st.markdown(f"### {icon} {tab_type}")
    
    # Message input
    label = "Message you received:" if is_received else "Message you want to send:"
    msg = st.text_area(
        label, 
        value=st.session_state.active_msg, 
        height=120, 
        key="translate_msg" if is_received else "coach_msg",
        help="Enter the message for analysis"
    )
    
    # Efficient character count
    st.caption(f"Characters: {len(msg)}")
    
    # Context selector
    ctx = render_context_selector("2" if is_received else "")
    
    # Analysis button
    button_text = "🔍 Analyze Message" if is_received else "✨ Improve Message"
    
    if st.button(button_text, type="primary", disabled=not msg.strip()):
        if not msg.strip():
            st.error("Please enter a message to analyze")
            return
        
        # Update active state
        st.session_state.active_msg = msg
        st.session_state.active_ctx = ctx
        
        # Show loading
        with st.spinner("Analyzing message..."):
            result = analyze_message(msg, ctx, is_received)
        
        # Display results efficiently
        if is_received:
            # Understanding results
            st.markdown(f'<div class="pos">Sentiment: {result["sentiment"].title()}</div>', 
                       unsafe_allow_html=True)
            st.markdown(f'<div class="neu">Emotion: {result["emotion"].title()}</div>', 
                       unsafe_allow_html=True)
            
            st.markdown(f'<div class="meaning-box"><strong>What they mean:</strong><br>{result["meaning"]}</div>', 
                       unsafe_allow_html=True)
            st.markdown(f'<div class="need-box"><strong>What they need:</strong><br>{result["need"]}</div>', 
                       unsafe_allow_html=True)
            st.markdown(f'<div class="ai-box"><strong>Suggested response:</strong><br>{result["response"]}</div>', 
                       unsafe_allow_html=True)
            
            # Copy button
            if st.button("📋 Copy Response", key="copy_response"):
                st.success("✅ Response copied to clipboard!")
        else:
            # Improvement results
            st.markdown(f'<div class="pos">Current sentiment: {result["sentiment"].title()}</div>', 
                       unsafe_allow_html=True)
            st.markdown(f'<div class="neu">Current emotion: {result["emotion"].title()}</div>', 
                       unsafe_allow_html=True)
            st.markdown(f'<div class="ai-box"><strong>Improved version:</strong><br>{result["reframed"]}</div>', 
                       unsafe_allow_html=True)
            
            # Copy button
            if st.button("📋 Copy Improved Message", key="copy_improved"):
                st.success("✅ Improved message copied to clipboard!")
        
        # Save to history efficiently
        history_entry = {
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'receive' if is_received else 'send',
            'context': ctx,
            'original': msg,
            'sentiment': result['sentiment'],
            'emotion': result['emotion'],
            'result': result
        }
        
        st.session_state.history.append(history_entry)
        
        # Limit history size for memory efficiency
        if len(st.session_state.history) > 100:
            st.session_state.history = st.session_state.history[-100:]

# Main app
def main():
    """Optimized main function"""
    st.title("🎙️ The Third Voice")
    st.markdown("*Your communication coach for better relationships*")
    
    # Sidebar
    render_quota_sidebar()
    render_history_sidebar()
    
    # Main tabs
    tab1, tab2 = st.tabs(["📥 Understand Messages", "📤 Improve Messages"])
    
    with tab1:
        render_analysis_tab(is_received=True)
    
    with tab2:
        render_analysis_tab(is_received=False)

if __name__ == "__main__":
    main()
