import streamlit as st
import google.generativeai as genai
import json
import datetime
import re
import time

# Optimized session state init
defaults = {'token_validated': False, 'api_key': st.secrets.get("GEMINI_API_KEY", ""), 'count': 0, 'history': [], 'active_msg': '', 'active_ctx': 'general', 'current_tab': 0}
for key, default in defaults.items():
    if key not in st.session_state: st.session_state[key] = default

# Token validation
if not st.session_state.token_validated:
    token = st.text_input("🔑 Beta Token:", type="password")
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]: 
        st.session_state.token_validated = True
        st.success("✅ Welcome!")
        st.rerun()
    elif token: st.error("❌ Invalid token")
    if not st.session_state.token_validated: st.stop()

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")

# Enhanced CSS with swipe navigation and full screen tabs
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

/* Full screen tabs and swipe navigation */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    width: 100%;
    justify-content: stretch;
}

.stTabs [data-baseweb="tab"] {
    flex: 1;
    white-space: nowrap;
    background-color: #f0f2f6;
    border-radius: 8px 8px 0 0;
    margin: 0 2px;
    padding: 12px 16px;
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: #e6e9ef;
    transform: translateY(-2px);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #ffffff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-bottom: 3px solid #4CAF50;
}

.stTabs [data-baseweb="tab-panel"] {
    padding: 20px;
    min-height: 70vh;
    background-color: #ffffff;
    border-radius: 0 0 8px 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Swipe navigation container */
.tab-container {
    position: relative;
    width: 100%;
    overflow: hidden;
    touch-action: pan-x;
}

.tab-content {
    display: flex;
    transition: transform 0.3s ease;
    width: 300%;
}

.tab-pane {
    width: 33.333%;
    padding: 20px;
    min-height: 70vh;
    box-sizing: border-box;
}

/* Swipe indicators */
.swipe-indicator {
    position: absolute;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 8px;
    z-index: 10;
}

.swipe-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #ccc;
    transition: background-color 0.3s ease;
}

.swipe-dot.active {
    background-color: #4CAF50;
}

/* Navigation buttons */
.nav-buttons {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 20px 0;
    padding: 0 20px;
}

.nav-btn {
    background: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 25px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}

.nav-btn:hover {
    background: #45a049;
    transform: translateY(-2px);
}

.nav-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
    transform: none;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 10px 12px;
    }
    
    .tab-pane {
        padding: 15px;
    }
    
    .nav-buttons {
        padding: 0 10px;
    }
}

/* Touch gestures hint */
.touch-hint {
    text-align: center;
    color: #666;
    font-size: 12px;
    margin: 10px 0;
    opacity: 0.7;
}

/* Dark theme support */
[data-theme="dark"] .stTabs [data-baseweb="tab"] {
    background-color: #2d3748;
    color: #e2e8f0;
}

[data-theme="dark"] .stTabs [data-baseweb="tab"]:hover {
    background-color: #4a5568;
}

[data-theme="dark"] .stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #1a202c;
    color: #ffffff;
}

[data-theme="dark"] .stTabs [data-baseweb="tab-panel"] {
    background-color: #1a202c;
    color: #e2e8f0;
}
</style>"""

st.markdown(get_css(), unsafe_allow_html=True)

# JavaScript for swipe functionality
swipe_js = """
<script>
let startX = 0;
let currentX = 0;
let isDragging = false;
let currentTab = 0;

function initSwipeNavigation() {
    const tabContainer = document.querySelector('.tab-container');
    const tabContent = document.querySelector('.tab-content');
    
    if (!tabContainer || !tabContent) {
        setTimeout(initSwipeNavigation, 100);
        return;
    }
    
    // Touch events
    tabContainer.addEventListener('touchstart', handleTouchStart, { passive: false });
    tabContainer.addEventListener('touchmove', handleTouchMove, { passive: false });
    tabContainer.addEventListener('touchend', handleTouchEnd);
    
    // Mouse events for desktop
    tabContainer.addEventListener('mousedown', handleMouseDown);
    tabContainer.addEventListener('mousemove', handleMouseMove);
    tabContainer.addEventListener('mouseup', handleMouseEnd);
    tabContainer.addEventListener('mouseleave', handleMouseEnd);
    
    // Prevent default drag behavior
    tabContainer.addEventListener('dragstart', (e) => e.preventDefault());
}

function handleTouchStart(e) {
    startX = e.touches[0].clientX;
    isDragging = true;
}

function handleTouchMove(e) {
    if (!isDragging) return;
    e.preventDefault();
    currentX = e.touches[0].clientX;
    const deltaX = currentX - startX;
    updateTabPosition(deltaX);
}

function handleTouchEnd() {
    if (!isDragging) return;
    isDragging = false;
    const deltaX = currentX - startX;
    const threshold = 50;
    
    if (Math.abs(deltaX) > threshold) {
        if (deltaX > 0 && currentTab > 0) {
            changeTab(currentTab - 1);
        } else if (deltaX < 0 && currentTab < 2) {
            changeTab(currentTab + 1);
        } else {
            resetTabPosition();
        }
    } else {
        resetTabPosition();
    }
}

function handleMouseDown(e) {
    startX = e.clientX;
    isDragging = true;
    e.preventDefault();
}

function handleMouseMove(e) {
    if (!isDragging) return;
    currentX = e.clientX;
    const deltaX = currentX - startX;
    updateTabPosition(deltaX);
}

function handleMouseEnd() {
    if (!isDragging) return;
    isDragging = false;
    const deltaX = currentX - startX;
    const threshold = 50;
    
    if (Math.abs(deltaX) > threshold) {
        if (deltaX > 0 && currentTab > 0) {
            changeTab(currentTab - 1);
        } else if (deltaX < 0 && currentTab < 2) {
            changeTab(currentTab + 1);
        } else {
            resetTabPosition();
        }
    } else {
        resetTabPosition();
    }
}

function updateTabPosition(deltaX) {
    const tabContent = document.querySelector('.tab-content');
    const baseTransform = -currentTab * 33.333;
    const dragTransform = (deltaX / window.innerWidth) * 33.333;
    tabContent.style.transform = `translateX(${baseTransform + dragTransform}%)`;
}

function resetTabPosition() {
    const tabContent = document.querySelector('.tab-content');
    tabContent.style.transform = `translateX(${-currentTab * 33.333}%)`;
}

function changeTab(newTab) {
    currentTab = newTab;
    const tabContent = document.querySelector('.tab-content');
    tabContent.style.transform = `translateX(${-currentTab * 33.333}%)`;
    
    // Update indicators
    updateIndicators();
    
    // Update Streamlit session state
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        key: 'current_tab',
        value: currentTab
    }, '*');
}

function updateIndicators() {
    const dots = document.querySelectorAll('.swipe-dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentTab);
    });
}

// Navigation button handlers
function goToPrevTab() {
    if (currentTab > 0) {
        changeTab(currentTab - 1);
    }
}

function goToNextTab() {
    if (currentTab < 2) {
        changeTab(currentTab + 1);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initSwipeNavigation);
setTimeout(initSwipeNavigation, 500);
</script>
"""

# API setup
if not st.session_state.api_key:
    st.warning("⚠️ API Key Required")
    key = st.text_input("Gemini API Key:", type="password")
    if st.button("Save") and key: 
        st.session_state.api_key = key
        st.success("✅ Saved!")
        st.rerun()
    st.stop()

@st.cache_resource
def get_ai():
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Cached quota info
@st.cache_data(ttl=60)
def get_quota_info():
    daily_limit = 1500
    current_usage = st.session_state.count
    remaining = max(0, daily_limit - current_usage)
    return current_usage, remaining, daily_limit

def clean_json_response(text):
    text = re.sub(r'```json\s*|\s*```', '', text)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    return json_match.group(0) if json_match else text

def get_offline_analysis(msg, ctx, is_received=False):
    positive_words = ['good', 'great', 'happy', 'love', 'awesome', 'excellent', 'wonderful', 'amazing', 'perfect', 'thank']
    negative_words = ['bad', 'hate', 'angry', 'sad', 'terrible', 'awful', 'horrible', 'upset', 'mad', 'disappointed']
    
    msg_lower = msg.lower()
    pos_count = sum(1 for word in positive_words if word in msg_lower)
    neg_count = sum(1 for word in negative_words if word in msg_lower)
    
    sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"
    
    # Emotion detection
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
    current_usage, remaining, daily_limit = get_quota_info()
    
    if remaining <= 0:
        st.warning(f"⚠️ Daily quota reached ({current_usage}/{daily_limit}). Using offline mode.")
        return get_offline_analysis(msg, ctx, is_received)
    
    # Unified prompt template
    if is_received:
        prompt = f'''Context: {ctx}. Analyze this received message: "{msg}"
Return JSON with keys: sentiment, emotion, meaning, need, response'''
    else:
        prompt = f'''Context: {ctx}. Help reframe this message: "{msg}"
Return JSON with keys: sentiment, emotion, reframed'''
    
    try:
        result = get_ai().generate_content(prompt)
        cleaned_text = clean_json_response(result.text)
        parsed_result = json.loads(cleaned_text)
        
        # Validate required keys
        required_keys = ['sentiment', 'emotion', 'meaning', 'need', 'response'] if is_received else ['sentiment', 'emotion', 'reframed']
        
        for key in required_keys:
            if key not in parsed_result or not parsed_result[key]:
                raise ValueError(f"Missing key: {key}")
        
        return parsed_result
        
    except Exception as e:
        # Handle quota errors
        if "429" in str(e) or "quota" in str(e).lower():
            st.error("🚫 **API Quota Exceeded**")
            st.info("**Solutions:** Wait (reset at midnight PST), Upgrade to paid plan, or Use offline mode")
            return get_offline_analysis(msg, ctx, is_received)
        
        st.error(f"Analysis error: {str(e)}")
        
        # Retry logic
        if retry_count < 2:
            time.sleep(1)
            return analyze(msg, ctx, is_received, retry_count + 1)
        
        return get_offline_analysis(msg, ctx, is_received)

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
    # Upload/Download
    uploaded = st.sidebar.file_uploader("📤 Load History", type="json")
    if uploaded:
        try:
            st.session_state.history = json.load(uploaded)
            st.sidebar.success("✅ Loaded!")
        except:
            st.sidebar.error("❌ Invalid file")

    if st.session_state.history:
        st.sidebar.download_button("💾 Save", 
                                  json.dumps(st.session_state.history, indent=2), 
                                  f"history_{datetime.datetime.now().strftime('%m%d_%H%M')}.json")
        
        # Session history
        st.sidebar.markdown("📜 **This Session**")
        for i, entry in enumerate(st.session_state.history[-5:]):
            real_idx = len(st.session_state.history) - 5 + i
            if st.sidebar.button(f"#{real_idx+1} {entry['context'][:3]} ({entry['time'][-5:]})", 
                               key=f"load_{real_idx}"):
                load_conversation(real_idx)
                st.rerun()

def render_context_selector(key_suffix=""):
    contexts = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
    return st.selectbox("Context:", contexts, 
                       index=contexts.index(st.session_state.active_ctx), 
                       key=f"ctx{key_suffix}")

def render_analysis_tab(is_received=False):
    tab_type = "Understand Message" if is_received else "Improve Message"
    st.markdown(f"### {tab_type}")
    
    msg = st.text_area("Received:" if is_received else "Message:", 
                      value=st.session_state.active_msg, 
                      height=120, 
                      key="translate_msg" if is_received else "coach_msg")
    
    ctx = render_context_selector("2" if is_received else "")
    
    if st.button("🔍 Analyze" if is_received else "🚀 Analyze", type="primary") and msg.strip():
        with st.spinner(f"Analyzing {'the received' if is_received else 'your'} message..."):
            st.session_state.count += 1
            result = analyze(msg, ctx, is_received)
            sentiment = result.get("sentiment", "neutral")
            
            # Sentiment display
            st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', 
                       unsafe_allow_html=True)
            
            if is_received:
                # Meaning analysis
                meaning = result.get('meaning', 'Unable to analyze')
                box_class = "offline-box" if "📴 **Offline Analysis:**" in meaning else "meaning-box"
                st.markdown(f'<div class="{box_class}"><strong>💭 What they mean:</strong><br>{meaning}</div>', 
                           unsafe_allow_html=True)
                
                # Need analysis
                need = result.get('need', 'Unable to determine')
                st.markdown(f'<div class="need-box"><strong>🎯 What they need:</strong><br>{need}</div>', 
                           unsafe_allow_html=True)
                
                # Suggested response
                response = result.get("response", "I understand.")
                st.markdown(f'<div class="ai-box"><strong>💬 Suggested response:</strong><br>{response}</div>', 
                           unsafe_allow_html=True)
                
                display_result = response
            else:
                # Improved message
                improved = result.get("reframed", msg)
                st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)
                display_result = improved
            
            if st.button("📋 Copy", key=f"copy_btn_{'translate' if is_received else 'coach'}", 
                        help="Copy to clipboard"):
                st.success("✅ Copied to clipboard!")
            
            # Save to history
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

def render_navigation_controls():
    """Render navigation buttons and swipe indicators"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", key="prev_btn", 
                    disabled=st.session_st
