import streamlit as st
import google.generativeai as genai
import json
import datetime

# --- Efficient Token System ---
if 'token_validated' not in st.session_state:
    token = st.text_input("🔑 Beta Token:", type="password", placeholder="Enter your beta token")
    if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
        st.session_state.token_validated = True
        st.success("✅ Welcome to The Third Voice Beta!")
        st.rerun()
    elif token: 
        st.error("❌ Invalid token. Contact hello@thethirdvoice.ai")
    if not st.session_state.token_validated: st.stop()

# --- Mobile-First Config ---
st.set_page_config(page_title="The Third Voice", page_icon="🎙️")

# --- Minimal CSS ---
st.markdown("""<style>
.ai-box { background: #f0f8ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #4CAF50; }
.pos { background: #d4edda; padding: 0.5rem; border-radius: 5px; color: #155724; }
.neg { background: #f8d7da; padding: 0.5rem; border-radius: 5px; color: #721c24; }
.neu { background: #d1ecf1; padding: 0.5rem; border-radius: 5px; color: #0c5460; }
</style>""", unsafe_allow_html=True)

# --- Initialize ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")
if 'count' not in st.session_state:
    st.session_state.count = 0
if 'history' not in st.session_state:
    st.session_state.history = []

# --- API Setup ---
if not st.session_state.api_key:
    st.warning("⚠️ API Key Required")
    key = st.text_input("Gemini API Key:", type="password", help="Get free key: aistudio.google.com")
    if st.button("Save") and key:
        st.session_state.api_key = key
        st.success("✅ Saved!")
        st.rerun()
    st.stop()

# --- AI Coach Class (Streamlined) ---
@st.cache_resource
def get_ai():
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_ai()

def analyze_and_reframe(message, context, is_received=False):
    """Single function for both analyze and reframe"""
    try:
        if is_received:
            # For received messages - analyze + suggest response
            prompt = f"""Context: {context} relationship.
            
Analyze this received message and suggest how to respond:

Message: "{message}"

Return JSON:
{{
  "sentiment": "positive/negative/neutral",
  "emotion": "main emotion",
  "meaning": "what they really mean",
  "need": "what they need",
  "response": "suggested response for {context} context"
}}"""
        else:
            # For sending messages - analyze + reframe
            prompt = f"""Context: {context} relationship.
            
Analyze and reframe this message to be more constructive:

Message: "{message}"

Return JSON:
{{
  "sentiment": "positive/negative/neutral",
  "emotion": "main emotion", 
  "reframed": "better version for {context} context"
}}"""
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except:
        # Fallback
        if is_received:
            return {"sentiment": "neutral", "emotion": "mixed", "meaning": "Processing...", "need": "Understanding", "response": "I understand. Can we talk about this?"}
        else:
            return {"sentiment": "neutral", "emotion": "mixed", "reframed": f"I'd like to discuss: {message}"}

# --- Header ---
st.markdown("# 🎙️ The Third Voice")
st.markdown("*AI co-mediator for better communication*")
st.sidebar.markdown(f"**Calls:** {st.session_state.count}/1500")

# --- Main Tabs ---
tab1, tab2 = st.tabs(["📤 Message Coach", "📥 Message Translator"])

with tab1:
    st.markdown("### Improve Your Message")
    
    message = st.text_area("Message to send:", height=80, placeholder="Type your message...")
    context = st.selectbox("Relationship:", ["general", "romantic", "coparenting", "workplace", "family", "friend"])
    
    if st.button("🚀 Analyze & Improve", type="primary"):
        if message.strip():
            with st.spinner("🤖 AI working..."):
                st.session_state.count += 1
                result = analyze_and_reframe(message, context)
                
                # Display results
                sentiment = result.get("sentiment", "neutral")
                st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
                
                st.markdown("**🔄 Improved Version:**")
                improved = result.get("reframed", message)
                st.markdown(f'<div class="ai-box">{improved}</div>', unsafe_allow_html=True)
                
                # Save to history
                st.session_state.history.append({
                    "time": datetime.datetime.now().strftime("%H:%M"),
                    "type": "send",
                    "context": context,
                    "original": message,
                    "result": improved
                })
                
                st.code(improved, language="text")
        else:
            st.warning("Please enter a message")

with tab2:
    st.markdown("### Understand Received Message")
    
    received = st.text_area("Message you received:", height=80, placeholder="Paste the message...")
    context = st.selectbox("Your relationship:", ["general", "romantic", "coparenting", "workplace", "family", "friend"], key="context2")
    
    if st.button("🔍 Analyze & Respond", type="primary"):
        if received.strip():
            with st.spinner("🤖 AI translating..."):
                st.session_state.count += 1
                result = analyze_and_reframe(received, context, is_received=True)
                
                # Display analysis
                sentiment = result.get("sentiment", "neutral")
                st.markdown(f'<div class="{sentiment[:3]}">{sentiment.title()} • {result.get("emotion", "mixed").title()}</div>', unsafe_allow_html=True)
                
                st.markdown("**🧠 What they mean:**")
                st.markdown(result.get("meaning", "Processing..."))
                
                st.markdown("**💭 What they need:**")
                st.markdown(result.get("need", "Understanding"))
                
                st.markdown("**💬 Suggested response:**")
                response = result.get("response", "I understand.")
                st.markdown(f'<div class="ai-box">{response}</div>', unsafe_allow_html=True)
                
                # Save to history
                st.session_state.history.append({
                    "time": datetime.datetime.now().strftime("%H:%M"),
                    "type": "receive",
                    "context": context,
                    "original": received,
                    "result": response
                })
                
                st.code(response, language="text")
        else:
            st.warning("Please enter a message")

# --- Quick History ---
if st.session_state.history:
    with st.expander("📜 Recent History"):
        for entry in st.session_state.history[-5:]:  # Last 5 only
            icon = "📤" if entry["type"] == "send" else "📥"
            st.markdown(f"**{icon} {entry['time']} ({entry['context']})**")
            st.markdown(f"*Original:* {entry['original'][:50]}...")
            st.markdown(f"*Result:* {entry['result'][:50]}...")
            st.markdown("---")
        
        # Download option
        if st.button("💾 Download Full History"):
            history_json = json.dumps(st.session_state.history, indent=2)
            st.download_button(
                "📥 Save History",
                history_json,
                f"third_voice_{datetime.datetime.now().strftime('%m%d_%H%M')}.json",
                "application/json"
            )

# --- Footer ---
st.markdown("---")
st.markdown("*Built with ❤️ by Predrag • Beta v0.9 • Feedback: hello@thethirdvoice.ai*")
