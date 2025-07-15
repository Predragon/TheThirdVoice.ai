import streamlit as st
import google.generativeai as genai
import json
from typing import Dict
import datetime

# --- Beta Tester Token Validation ---
valid_tokens = ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]
if 'token_validated' not in st.session_state:
    st.session_state.token_validated = False

if not st.session_state.token_validated:
    with st.form("token_form"):
        st.markdown("### Welcome to The Third Voice Beta")
        token_input = st.text_input("Enter Beta Tester Token:", type="password", help="Contact hello@thethirdvoice.ai for a token.")
        submit_token = st.form_submit_button("Validate Token")
        if submit_token:
            if token_input in valid_tokens:
                st.session_state.token_validated = True
                st.success("✅ Token validated! Welcome to The Third Voice beta.")
                st.rerun()
            else:
                st.error("❌ Invalid token. Please contact hello@thethirdvoice.ai.")
    st.stop()

# --- Configuration and Setup ---
st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide", initial_sidebar_state="collapsed")

# --- Simplified CSS ---
st.markdown("""
<style>
.main-header { text-align: center; background: linear-gradient(45deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }
.ai-response { background: #f0f8ff; border-left: 4px solid #4CAF50; padding: 1rem; margin: 1rem 0; border-radius: 5px; }
.sentiment-positive { background: #d4edda; color: #155724; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #28a745; }
.sentiment-negative { background: #f8d7da; color: #721c24; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #dc3545; }
.sentiment-neutral { background: #d1ecf1; color: #0c5460; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #17a2b8; }
</style>
""", unsafe_allow_html=True)

# --- API Key Initialization ---
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

# --- API Key Configuration UI ---
if not st.session_state.gemini_api_key:
    with st.expander("🔑 Configure Google Gemini API", expanded=True):
        st.markdown("**Get your free API key from:** [Google AI Studio](https://aistudio.google.com/app/apikey)")
        api_key_input = st.text_input("Enter your Gemini API key:", type="password")
        if st.button("Save API Key") and api_key_input:
            st.session_state.gemini_api_key = api_key_input
            st.success("✅ API key saved!")
            st.rerun()

# --- Helper Functions ---
def load_history_context(key):
    uploaded_file = st.file_uploader("Upload Saved History (optional)", type="json", key=key)
    if uploaded_file:
        try:
            history_data = json.load(uploaded_file)
            st.success("✅ History uploaded!")
            return "\n".join([f"[{entry['timestamp']}] {entry['context']}: {entry['original']} -> {entry['reframed']}" for entry in history_data])
        except:
            st.error("❌ Invalid history file.")
    return ""

def display_analysis(analysis_result, reframed):
    if analysis_result.get("success"):
        sentiment = analysis_result.get("sentiment", "neutral")
        css_class = f"sentiment-{sentiment}"
        st.markdown(f'<div class="{css_class}">Sentiment: {sentiment.title()} ({analysis_result.get("confidence", 0.5):.1%})</div>', unsafe_allow_html=True)
        st.markdown(f"**Primary emotion:** {analysis_result.get('primary_emotion', 'mixed').title()}")
        if tone := analysis_result.get("tone"):
            st.markdown(f"**Tone:** {tone}")
        if triggers := analysis_result.get("potential_triggers", []):
            st.markdown("**Potential triggers:**")
            for trigger in triggers:
                st.markdown(f"• {trigger}")
    else:
        st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
    st.markdown('<div class="ai-response">' + reframed + '</div>', unsafe_allow_html=True)

# --- GeminiMessageCoach Class ---
class GeminiMessageCoach:
    def __init__(self):
        self.model = None

    def _get_model(self):
        if not self.model and st.session_state.get('gemini_api_key'):
            try:
                genai.configure(api_key=st.session_state.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                st.error(f"Failed to configure Gemini API: {e}")
        return self.model

    def analyze_message(self, message: str, history_context: str = "") -> Dict:
        model = self._get_model()
        if not model:
            return {"success": False, "error": "API key not configured"}

        try:
            prompt = f"""
            Previous conversation: {history_context}
            
            Analyze this message sentiment and emotions. Return JSON with:
            1. sentiment: "positive", "negative", or "neutral"
            2. confidence: 0.0 to 1.0
            3. primary_emotion: main emotion
            4. tone: overall tone
            5. potential_triggers: problematic phrases
            
            Message: "{message}"
            Return only valid JSON.
            """
            response = model.generate_content(prompt)
            try:
                result = json.loads(response.text)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                return {"success": True, "sentiment": "neutral", "confidence": 0.8, "primary_emotion": "mixed", "tone": "Analysis completed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reframe_message(self, message: str, context: str = "general", history_context: str = "") -> str:
        model = self._get_model()
        if not model:
            return self._fallback_reframe(message, context)

        try:
            context_map = {
                "romantic": "Focus on love and partnership. Use warm, caring language.",
                "coparenting": "Focus on children's wellbeing. Use collaborative language.",
                "workplace": "Use professional, solution-focused language.",
                "general": "Use diplomatic, empathetic language."
            }
            
            prompt = f"""
            Previous conversation: {history_context}
            
            Rewrite this message to be positive, constructive, and emotionally intelligent.
            Context: {context} - {context_map.get(context, context_map["general"])}
            
            Original: "{message}"
            
            Rules: Maintain intent, remove accusations, use "I" statements, add empathy, focus on solutions.
            Return only the reframed message.
            """
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return self._fallback_reframe(message, context)

    def _fallback_reframe(self, message: str, context: str) -> str:
        reframed = message.replace("you always", "I've noticed").replace("you never", "it would help if")
        if context == "coparenting":
            return f"For our child's sake, {reframed.lower()}. Can we work together?"
        elif context == "romantic":
            return f"I care about us, and {reframed.lower()}. Can we talk?"
        return f"I'd like to share: {reframed.lower()}. Can we discuss this?"

    def emotional_translation(self, message: str, history_context: str = "") -> str:
        model = self._get_model()
        if not model:
            return "API not configured. Please add your Gemini API key."
        try:
            prompt = f"""
            Previous conversation: {history_context}
            
            Translate this message emotionally. Explain:
            1. What emotions the sender feels
            2. What they really mean
            3. How to respond
            4. What they need
            
            Message: "{message}"
            Be empathetic and build understanding.
            """
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Translation unavailable: {str(e)}"

# --- App Session State ---
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'history' not in st.session_state:
    st.session_state.history = []

@st.cache_resource
def get_ai_coach():
    return GeminiMessageCoach()

ai_coach = get_ai_coach()

# --- App Header ---
st.markdown("""
<div class="main-header">
    <h1>🎙️ The Third Voice</h1>
    <h3>Your AI co-mediator for emotionally intelligent communication</h3>
    <p><i>Built in detention, with a phone, for life's hardest moments.</i></p>
    <p>⚡ <strong>Powered by Google Gemini Flash</strong></p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown(f"**API Calls:** {st.session_state.usage_count}/1500")
st.sidebar.info("Beta testing • Feedback: hello@thethirdvoice.ai")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["💬 Message Coach", "🗣️ Emotional Translator", "💡 About & Models", "📜 History"])

with tab1:
    st.markdown("### AI-Powered Message Coaching")
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please configure your Gemini API key above.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        history_context = load_history_context("tab1")
        message_input = st.text_area("Your message draft:", placeholder="Type the message you want to send...", height=100)
        context = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace"])
        
        if st.button("⚡ AI Analysis & Reframe", type="primary"):
            if message_input.strip():
                with st.spinner("⚡ AI analyzing..."):
                    st.session_state.usage_count += 1
                    analysis_result = ai_coach.analyze_message(message_input, history_context)
                    reframed = ai_coach.reframe_message(message_input, context, history_context)
                    
                    st.session_state.history.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "original": message_input,
                        "context": context,
                        "sentiment": analysis_result.get("sentiment", "neutral"),
                        "reframed": reframed
                    })
                    
                    with col2:
                        st.markdown("#### ⚡ AI Analysis & Reframe")
                        display_analysis(analysis_result, reframed)
                        st.code(reframed, language="text")
            else:
                st.warning("Please enter a message.")

with tab2:
    st.markdown("### AI Emotional Translation")
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please configure your Gemini API key above.")
    
    history_context = load_history_context("tab2")
    received_message = st.text_area("Message you received:", placeholder="Paste the message you're trying to understand...", height=100)
    
    if st.button("⚡ AI Translate", type="primary"):
        if received_message.strip():
            with st.spinner("⚡ AI analyzing emotional subtext..."):
                st.session_state.usage_count += 1
                translation = ai_coach.emotional_translation(received_message, history_context)
                st.markdown("#### 🗣️ AI Emotional Translation")
                st.markdown(f"**Original:** \"{received_message}\"")
                st.markdown('<div class="ai-response">' + translation + '</div>', unsafe_allow_html=True)
                
                st.session_state.history.append({
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "original": received_message,
                    "context": "translation",
                    "sentiment": "N/A",
                    "reframed": translation
                })
        else:
            st.warning("Please enter a message.")

with tab3:
    st.markdown("### 💡 About The Third Voice")
    st.markdown("""
**The Third Voice** is an AI-powered co-mediator for emotionally intelligent communication.

**Created by:** Predrag Mirkovic  
**Built:** In detention, on a phone, for people in emotional pain  
**Tech Stack:** Streamlit + Google Gemini Flash  

**Use cases:** Romantic conflict • Co-parenting issues • Workplace misunderstandings

### 🤖 AI Models
- **Model:** `gemini-1.5-flash`
- **Capabilities:** Sentiment analysis, emotional reframing, communication coaching
- **Limits:** 15 requests/min • 1500/day (free tier)
- **Setup:** [Google AI Studio](https://aistudio.google.com/app/apikey)
""")

with tab4:
    st.markdown("### 📜 Conversation History")
    
    history_data = st.session_state.history
    uploaded_file = st.file_uploader("Upload Saved History", type="json", key="tab4")
    if uploaded_file:
        try:
            history_data = json.load(uploaded_file)
            st.success("✅ History uploaded!")
        except:
            st.error("❌ Invalid history file.")
    
    if history_data:
        conversation_options = [f"[{entry['timestamp']}] {entry['context']}: {entry['original'][:50]}..." for entry in history_data]
        selected_conversation = st.selectbox("Select conversation:", ["None"] + conversation_options)
        
        if selected_conversation != "None":
            selected_index = conversation_options.index(selected_conversation)
            selected_entry = history_data[selected_index]
            st.markdown(f"**Selected ({selected_entry['context']}):**")
            st.markdown(f"**Original:** {selected_entry['original']}")
            st.markdown(f"**Sentiment:** {selected_entry['sentiment'].title()}")
            st.markdown(f"**Reframed:** {selected_entry['reframed']}")
            
            new_message = st.text_area("Reply to this conversation:", height=100)
            context = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace"], 
                                 index=["general", "romantic", "coparenting", "workplace"].index(selected_entry['context']) 
                                 if selected_entry['context'] in ["general", "romantic", "coparenting", "workplace"] else 0)
            
            if st.button("⚡ Analyze & Reframe Reply", type="primary"):
                if new_message.strip():
                    with st.spinner("⚡ AI analyzing reply..."):
                        st.session_state.usage_count += 1
                        history_context = f"Previous: {selected_entry['original']} -> {selected_entry['reframed']}"
                        analysis_result = ai_coach.analyze_message(new_message, history_context)
                        reframed = ai_coach.reframe_message(new_message, context, history_context)
                        
                        st.session_state.history.append({
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "original": new_message,
                            "context": context,
                            "sentiment": analysis_result.get("sentiment", "neutral"),
                            "reframed": reframed
                        })
                        
                        st.markdown("#### ✨ AI Analysis & Reframe")
                        display_analysis(analysis_result, reframed)
                        st.code(reframed, language="text")
        else:
            for entry in history_data:
                st.markdown(f"**[{entry['timestamp']}] {entry['context']}**")
                st.markdown(f"**Original:** {entry['original']}")
                st.markdown(f"**Sentiment:** {entry['sentiment'].title()}")
                st.markdown(f"**Reframed:** {entry['reframed']}")
                st.markdown("---")
    else:
        st.info("No conversation history yet. Analyze a message to start!")
    
    # Download history
    history_json = json.dumps(st.session_state.history, indent=2)
    st.download_button(
        label="📥 Save History",
        data=history_json,
        file_name=f"third_voice_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json"
            )
