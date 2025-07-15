import streamlit as st import google.generativeai as genai import json import datetime import re import time

--- Constants ---

POSITIVE_WORDS = ['good', 'great', 'happy', 'love', 'awesome', 'excellent', 'wonderful', 'amazing', 'perfect', 'thank'] NEGATIVE_WORDS = ['bad', 'hate', 'angry', 'sad', 'terrible', 'awful', 'horrible', 'upset', 'mad', 'disappointed'] EMOTION_MAP = { 'angry': ['angry', 'mad', 'furious'], 'sad': ['sad', 'disappointed', 'hurt'], 'happy': ['happy', 'excited', 'great'], 'anxious': ['worried', 'anxious', 'concerned'] } CONTEXT_INSIGHTS = { "romantic": "This appears to be a personal message that may involve feelings or relationship dynamics.", "coparenting": "This message likely relates to child-related matters or parenting coordination.", "workplace": "This seems to be a professional communication that may involve work tasks or relationships.", "family": "This appears to be a family-related message that may involve personal or domestic matters.", "friend": "This looks like a casual message between friends.", "general": "This is a general communication." } VALID_TOKENS = ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]

--- Initialize Session State ---

defaults = { 'token_validated': False, 'api_key': st.secrets.get("GEMINI_API_KEY", ""), 'count': 0, 'history': [], 'active_msg': '', 'active_ctx': 'general' } st.session_state.update({k: v for k, v in defaults.items() if k not in st.session_state})

--- Token Validation ---

if not st.session_state.token_validated: token = st.text_input("🔑 Beta Token:", type="password") if token in VALID_TOKENS: st.session_state.token_validated = True st.success("✅ Welcome!") st.rerun() elif token: st.error("❌ Invalid token") st.stop()

--- Page Config ---

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")

--- Cached CSS ---

@st.cache_data def get_css(): return """<style>.ai-box{background:#f0f8ff;padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0;color:#000}.pos{background:#d4edda;padding:0.5rem;border-radius:5px;color:#155724;margin:0.2rem 0;font-weight:bold}.neg{background:#f8d7da;padding:0.5rem;border-radius:5px;color:#721c24;margin:0.2rem 0;font-weight:bold}.neu{background:#d1ecf1;padding:0.5rem;border-radius:5px;color:#0c5460;margin:0.2rem 0;font-weight:bold}.meaning-box{background:#f8f9fa;padding:1rem;border-radius:8px;border-left:4px solid #17a2b8;margin:0.5rem 0;color:#000}.need-box{background:#fff3cd;padding:1rem;border-radius:8px;border-left:4px solid #ffc107;margin:0.5rem 0;color:#000}.error-box{background:#f8d7da;padding:1rem;border-radius:8px;border-left:4px solid #dc3545;margin:0.5rem 0;color:#721c24}.offline-box{background:#fff8dc;padding:1rem;border-radius:8px;border-left:4px solid #ff9800;margin:0.5rem 0;color:#000}[data-theme="dark"] .ai-box{background:#1e3a5f;color:#fff}[data-theme="dark"] .pos{background:#2d5a3d;color:#90ee90}[data-theme="dark"] .neg{background:#5a2d2d;color:#ffb3b3}[data-theme="dark"] .neu{background:#2d4a5a;color:#87ceeb}[data-theme="dark"] .meaning-box{background:#2d4a5a;color:#87ceeb}[data-theme="dark"] .need-box{background:#5a5a2d;color:#ffeb3b}[data-theme="dark"] .offline-box{background:#5a4d2d;color:#ffeb3b}</style>"""

st.markdown(get_css(), unsafe_allow_html=True)

--- API Key Setup ---

if not st.session_state.api_key: st.warning("⚠️ API Key Required") key = st.text_input("Gemini API Key:", type="password") if st.button("Save") and key: st.session_state.api_key = key st.success("✅ Saved!") st.rerun() st.stop()

--- AI Setup ---

@st.cache_resource def get_ai(): genai.configure(api_key=st.session_state.api_key) return genai.GenerativeModel('gemini-1.5-flash')

@st.cache_data(ttl=60) def get_quota_info(): daily_limit = 1500 current_usage = st.session_state.count remaining = max(0, daily_limit - current_usage) return current_usage, remaining, daily_limit

--- Utilities ---

def clean_json_response(text): text = re.sub(r'json\s*|\s*', '', text) json_match = re.search(r'{.*}', text, re.DOTALL) return json_match.group(0) if json_match else text

def get_offline_analysis(msg, ctx, is_received=False): msg_lower = msg.lower() pos_count = sum(1 for word in POSITIVE_WORDS if word in msg_lower) neg_count = sum(1 for word in NEGATIVE_WORDS if word in msg_lower) sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral" emotion = "neutral" for e, words in EMOTION_MAP.items(): if any(word in msg_lower for word in words): emotion = e break if is_received: return { "sentiment": sentiment, "emotion": emotion, "meaning": f"📴 Offline Analysis: {CONTEXT_INSIGHTS.get(ctx)} The tone appears {sentiment} with {emotion} undertones.", "need": "More context needed for detailed analysis", "response": f"I understand you're sharing something important. Could you help me understand more about what you're looking for in this {ctx} situation?" } else: return { "sentiment": sentiment, "emotion": emotion, "reframed": f"📴 Offline Mode: Here's a basic reframe - Consider saying: 'I'd like to discuss something regarding our {ctx} situation: {msg[:80]}{'...' if len(msg) > 80 else ''}'" }

def analyze(msg, ctx, is_received=False, retry_count=0): current_usage, remaining, daily_limit = get_quota_info() if remaining <= 0: st.warning(f"⚠️ Daily quota reached ({current_usage}/{daily_limit}). Using offline mode.") return get_offline_analysis(msg, ctx, is_received) prompt = f'''Context: {ctx}. {'Analyze this received message' if is_received else 'Help reframe this message'}: "{msg}" Return JSON with keys: {'sentiment, emotion, meaning, need, response' if is_received else 'sentiment, emotion, reframed'}''' try: result = get_ai().generate_content(prompt) cleaned_text = clean_json_response(result.text) parsed_result = json.loads(cleaned_text) keys = ['sentiment', 'emotion', 'meaning', 'need', 'response'] if is_received else ['sentiment', 'emotion', 'reframed'] for key in keys: if key not in parsed_result or not parsed_result[key]: raise ValueError(f"Missing key: {key}") return parsed_result except Exception as e: if "429" in str(e) or "quota" in str(e).lower(): st.error("🚫 API Quota Exceeded") st.info("Solutions: Wait, upgrade plan, or use offline mode") return get_offline_analysis(msg, ctx, is_received) if retry_count < 2: time.sleep(1) return analyze(msg, ctx, is_received, retry_count + 1) st.error(f"Analysis error: {str(e)}") return get_offline_analysis(msg, ctx, is_received)

--- UI & Interaction Logic ---

def render_context_selector(): options = list(CONTEXT_INSIGHTS.keys()) return st.selectbox("Select Context", options, index=options.index(st.session_state.active_ctx))

def render_response(result, is_received): sentiment = result.get("sentiment", "neutral") emotion = result.get("emotion", "neutral").title() st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {emotion}</div>', unsafe_allow_html=True) if is_received: st.markdown(f'<div class="{"offline-box" if "📴" in result["meaning"] else "meaning-box"}"><strong>💭 What they mean:</strong><br>{result["meaning"]}</div>', unsafe_allow_html=True) st.markdown(f'<div class="need-box"><strong>🎯 What they need:</strong><br>{result["need"]}</div>', unsafe_allow_html=True) st.markdown(f'<div class="ai-box"><strong>💬 Suggested response:</strong><br>{result["response"]}</div>', unsafe_allow_html=True) return result["response"] else: st.markdown(f'<div class="ai-box">{result["reframed"]}</div>', unsafe_allow_html=True) return result["reframed"]

def render_analysis_tab(is_received=False): msg_key = "msg_received" if is_received else "msg_send" btn_label = "📥 Analyze Incoming" if is_received else "📤 Improve Message" st.subheader("Understand Incoming Message" if is_received else "Improve Outgoing Message") msg = st.text_area("Message:", value=st.session_state.active_msg, height=120, key=msg_key) ctx = render_context_selector() if st.button(btn_label): with st.spinner("Analyzing..."): st.session_state.count += 1 result = analyze(msg, ctx, is_received) output = render_response(result, is_received) st.session_state.history.append({ "time": datetime.datetime.now().strftime("%m/%d %H:%M"), "type": "receive" if is_received else "send", "context": ctx, "original": msg, "result": output, "sentiment": result.get("sentiment", "neutral") }) if is_received: st.session_state.history[-1].update({"meaning": result.get("meaning"), "need": result.get("need")})

def render_sidebar(): current_usage, remaining, daily_limit = get_quota_info() st.sidebar.markdown(f"API Quota: {current_usage}/{daily_limit} (Remaining: {remaining})") if remaining <= 100: st.sidebar.warning("⚠️ Low quota - offline mode may activate soon.") if uploaded := st.sidebar.file_uploader("Load History", type="json"): try: st.session_state.history = json.load(uploaded) st.sidebar.success("✅ History loaded.") except: st.sidebar.error("❌ Invalid file.") if st.session_state.history: st.sidebar.download_button("Save History", json.dumps(st.session_state.history, indent=2), file_name="ttv_history.json")

--- Render ---

st.image("logo.png", width=200) render_sidebar() tab1, tab2, tab3 = st.tabs(["📤 Coach", "📥 Translate", "ℹ️ About"]) with tab1: render_analysis_tab(is_received=False) with tab2: render_analysis_tab(is_received=True) with tab3: st.markdown("""### The Third Voice AI Communication Coach for emotionally intelligent interactions.

📤 Coach: Improve your messages before sending

📥 Translate: Understand messages you received

💾 Save/Load: History is session-based but exportable

🔒 Privacy: No cloud storage or user tracking


Beta v0.9.2 • Contact: hello@thethirdvoice.ai""")

