import streamlit as st
import google.generativeai as genai
import json
from typing import Dict
import datetime

# --- Beta Tester Token Validation ---
valid_tokens = ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]  # Add 50 tokens for testers
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
    st.stop()  # Stop app if token is invalid

# --- Configuration and Setup ---
st.set_page_config(
    page_title="The Third Voice",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-card { border: 2px solid #e0e0e0; border-radius: 10px; padding: 1.5rem; margin: 1rem 0; background: #f9f9f9; }
    .ai-response { background: #f0f8ff; border-left: 4px solid #4CAF50; padding: 1rem; margin: 1rem 0; border-radius: 5px; }
    .warning-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin: 1rem 0; border-radius: 5px; }
    .emotion-card { background: #e8f5e8; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #4CAF50; }
    .sentiment-positive { background: #d4edda; color: #155724; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #28a745; }
    .sentiment-negative { background: #f8d7da; color: #721c24; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #dc3545; }
    .sentiment-neutral { background: #d1ecf1; color: #0c5460; padding: 0.5rem; border-radius: 5px; border-left: 4px solid #17a2b8; }
</style>
""", unsafe_allow_html=True)

# --- API Key Initialization ---
api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", "")
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = api_key_from_secrets

api_key_loaded = bool(st.session_state.gemini_api_key)

# --- API Key Configuration UI ---
if not api_key_loaded:
    with st.expander("🔑 Configure Google Gemini API", expanded=True):
        st.markdown("**Get your free API key from:** [Google AI Studio](https://aistudio.google.com/app/apikey)")
        api_key_input = st.text_input(
            "Enter your Gemini API key:",
            value="",
            type="password",
            help="Your API key will be stored only in session memory."
        )
        if st.button("Save API Key"):
            if api_key_input:
                try:
                    genai.configure(api_key=api_key_input)
                    test_model = genai.GenerativeModel('gemini-1.5-flash')
                    test_model.generate_content("Test")
                    st.session_state.gemini_api_key = api_key_input
                    st.success("✅ API key saved and validated! You can now use all AI features.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to validate API key: {e}")
            else:
                st.warning("⚠️ Please enter a valid API key.")

# --- GeminiMessageCoach Class ---
class GeminiMessageCoach:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.model = None

    def _get_gemini_model(self):
        if not self.model and st.session_state.get('gemini_api_key'):
            try:
                genai.configure(api_key=st.session_state.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                st.error(f"Failed to configure Gemini API: {e}")
                return None
        return self.model

    def analyze_message(self, message: str, history_context: str = "") -> Dict:
        model = self._get_gemini_model()
        if not model:
            return {"success": False, "error": "API key not configured or model failed to initialize."}

        try:
            prompt = f"""
            Previous conversation history (for context):
            {history_context}

            Analyze this message for sentiment and emotions. Return a JSON response with:
            1. sentiment: "positive", "negative", or "neutral"
            2. confidence: number between 0.0 and 1.0
            3. primary_emotion: the main emotion detected
            4. emotions: list of emotions with scores
            5. tone: description of the overall tone
            6. potential_triggers: list of words/phrases that might cause negative reactions
            Message: "{message}"
            Return only valid JSON, no other text.
            """
            response = model.generate_content(prompt)
            try:
                result = json.loads(response.text)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                text = response.text.lower()
                sentiment = "negative" if any(w in text for w in ["negative", "angry", "frustrated"]) else \
                            "positive" if any(w in text for w in ["positive", "happy", "joy"]) else "neutral"
                return {
                    "success": True,
                    "sentiment": sentiment,
                    "confidence": 0.8,
                    "primary_emotion": "mixed",
                    "emotions": [],
                    "tone": "Analysis completed (fallback)",
                    "potential_triggers": [],
                    "raw_response": response.text
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reframe_message(self, message: str, context: str = "general", history_context: str = "") -> str:
        model = self._get_gemini_model()
        if not model:
            return self._fallback_reframe(message, context)

        try:
            context_instructions = {
                "romantic": "Focus on love, understanding, and partnership. Use warm, caring language.",
                "coparenting": "Focus on the children's wellbeing. Use collaborative, child-focused language.",
                "workplace": "Use professional, solution-focused language. Be respectful and constructive.",
                "general": "Use diplomatic, empathetic language that promotes understanding."
            }
            prompt = f"""
            Previous conversation history (for context):
            {history_context}

            Rewrite this message to be more positive, constructive, and emotionally intelligent.
            Context: {context}
            Instructions: {context_instructions.get(context, context_instructions["general"])}
            Original message: "{message}"
            Rules:
            1. Maintain the core message intent
            2. Remove accusatory language ("you always", "you never")
            3. Use "I" statements instead of "you" statements where possible
            4. Add empathy and understanding
            5. Focus on solutions, not problems
            6. Keep it natural and authentic
            7. Make it shorter if the original is too long
            Return only the reframed message, no other text.
            """
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return self._fallback_reframe(message, context)

    def _fallback_reframe(self, message: str, context: str) -> str:
        reframed = message.lower()
        reframed = reframed.replace("you always", "I've noticed sometimes")
        reframed = reframed.replace("you never", "it would help if we could")
        reframed = reframed.replace("always", "sometimes")
        reframed = reframed.replace("never", "rarely")
        if context == "coparenting":
            return f"For our child's sake, {reframed.capitalize()}. Can we work together on this?"
        elif context == "romantic":
            return f"I care about us, and {reframed.capitalize()}. Can we talk this through?"
        elif context == "workplace":
            return f"I’d like to address something: {reframed.capitalize()}. Can we discuss a solution?"
        else:
            return f"I’d like to share: {reframed.capitalize()}. Can we discuss this?"

    def emotional_translation(self, message: str, history_context: str = "") -> str:
        model = self._get_gemini_model()
        if not model:
            return "API not configured or model failed to initialize. Please add your Gemini API key."
        try:
            prompt = f"""
            Previous conversation history (for context):
            {history_context}

            Act as an emotional translator. Analyze this message and explain:
            1. What emotions the sender might be feeling
            2. What they might really mean beneath the surface
            3. How the receiver should respond
            4. What the sender might need right now
            Message: "{message}"
            Be empathetic and insightful. Focus on building understanding between people.
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
def get_ai_coach(api_key):
    return GeminiMessageCoach(api_key)

ai_coach = get_ai_coach(st.session_state.gemini_api_key)

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
st.sidebar.markdown(f"**API Calls Used:** {st.session_state.usage_count}/1500 daily")
st.sidebar.info("Welcome to The Third Voice beta! Analyze messages, save history locally, and share feedback at hello@thethirdvoice.ai.")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 AI Message Coach", "🗣️ Emotional Translator", "🤖 AI Models", "💡 About", "📜 History"])

with tab1:
    st.markdown("### AI-Powered Message Coaching")
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please configure your Gemini API key above to use AI features.")
    col1, col2 = st.columns([1, 1])
    with col1:
        # Upload history for context
        uploaded_file = st.file_uploader("Upload Saved History (optional)", type="json", help="Upload your saved history file to improve AI suggestions. Max 1MB.", accept_multiple_files=False, key="file_uploader_tab1")
        history_context = ""
        if uploaded_file:
            try:
                history_data = json.load(uploaded_file)
                history_context = "\n".join([f"[{entry['timestamp']}] {entry['context']}: {entry['original']} -> {entry['reframed']}" for entry in history_data])
                st.success("✅ History uploaded! AI will use it for context.")
            except:
                st.error("❌ Invalid history file. Please upload a valid JSON file.")
        
        message_input = st.text_area("Your message draft:", placeholder="Type the message you want to send...", height=100)
        context = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace"], index=0)
        if st.button("⚡ AI Analysis & Reframe", type="primary"):
            if message_input.strip():
                with st.spinner("⚡ AI is analyzing your message..."):
                    st.session_state.usage_count += 1
                    analysis_result = ai_coach.analyze_message(message_input, history_context)
                    reframed = ai_coach.reframe_message(message_input, context, history_context)
                    # Save to history
                    st.session_state.history.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "original": message_input,
                        "context": context,
                        "sentiment": analysis_result.get("sentiment", "neutral"),
                        "reframed": reframed
                    })
                    with col2:
                        st.markdown("#### ⚡ AI Analysis Results")
                        if analysis_result.get("success"):
                            sentiment = analysis_result.get("sentiment", "neutral")
                            confidence = analysis_result.get("confidence", 0.5)
                            css_class = {
                                "positive": "sentiment-positive",
                                "negative": "sentiment-negative",
                                "neutral": "sentiment-neutral"
                            }.get(sentiment, "sentiment-neutral")
                            st.markdown(f'<div class="{css_class}">Sentiment: {sentiment.title()} ({confidence:.1%} confidence)</div>', unsafe_allow_html=True)
                            st.markdown(f"**Primary emotion:** {analysis_result.get('primary_emotion', 'mixed').title()}")
                            if tone := analysis_result.get("tone"):
                                st.markdown(f"**Tone:** {tone}")
                            if triggers := analysis_result.get("potential_triggers", []):
                                st.markdown("**Potential triggers:**")
                                for trigger in triggers:
                                    st.markdown(f"• {trigger}")
                        else:
                            st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                        st.markdown("#### ✨ AI-Suggested Reframe")
                        st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                        st.markdown(reframed)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.code(reframed, language="text")
            else:
                st.warning("Please enter a message to analyze.")

with tab2:
    st.markdown("### AI Emotional Translation")
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please configure your Gemini API key above to use AI features.")
    # Upload history for context
    uploaded_file = st.file_uploader("Upload Saved History (optional)", type="json", help="Upload your saved history file to improve AI suggestions. Max 1MB.", accept_multiple_files=False,

with tab5:
    st.markdown("### 📜 Conversation History")
    # Upload history file
    uploaded_file = st.file_uploader("Upload Saved History (optional)", type="json", help="Upload your saved history file to continue a conversation. Max 1MB.", accept_multiple_files=False, key="file_uploader_tab5")
    history_data = st.session_state.history  # Default to in-session history
    if uploaded_file:
        try:
            history_data = json.load(uploaded_file)
            st.success("✅ History uploaded! Select a conversation below.")
        except:
            st.error("❌ Invalid history file. Please upload a valid JSON file.")
    
    # Display and select conversations
    if history_data:
        # Create a list of conversation summaries for the dropdown
        conversation_options = [f"[{entry['timestamp']}] {entry['context']}: {entry['original'][:50]}..." for entry in history_data]
        selected_conversation = st.selectbox("Select a conversation to continue:", ["None"] + conversation_options)
        if selected_conversation != "None":
            selected_index = conversation_options.index(selected_conversation)
            selected_entry = history_data[selected_index]
            st.markdown(f"**Selected Conversation ({selected_entry['context']}):**")
            st.markdown(f"**Original:** {selected_entry['original']}")
            st.markdown(f"**Sentiment:** {selected_entry['sentiment'].title()}")
            st.markdown(f"**Reframed:** {selected_entry['reframed']}")
            # Allow continuing the conversation
            new_message = st.text_area("Reply to this conversation:", placeholder="Type your next message...", height=100)
            context = st.selectbox("Context:", ["general", "romantic", "coparenting", "workplace"], index=["general", "romantic", "coparenting", "workplace"].index(selected_entry['context']) if selected_entry['context'] in ["general", "romantic", "coparenting", "workplace"] else 0)
            if st.button("⚡ Analyze & Reframe Reply", type="primary"):
                if new_message.strip():
                    with st.spinner("⚡ AI is analyzing your reply..."):
                        st.session_state.usage_count += 1
                        # Use selected conversation as context for AI
                        history_context = f"Previous conversation: {selected_entry['original']} -> {selected_entry['reframed']}"
                        analysis_result = ai_coach.analyze_message(new_message, history_context)
                        reframed = ai_coach.reframe_message(new_message, context, history_context)
                        # Save new message to history
                        st.session_state.history.append({
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "original": new_message,
                            "context": context,
                            "sentiment": analysis_result.get("sentiment", "neutral"),
                            "reframed": reframed
                        })
                        st.markdown("#### ✨ AI Analysis & Reframe")
                        if analysis_result.get("success"):
                            st.markdown(f"**Sentiment:** {analysis_result['sentiment'].title()} ({analysis_result['confidence']:.1%} confidence)")
                            st.markdown(f"**Primary emotion:** {analysis_result.get('primary_emotion', 'mixed').title()}")
                            if tone := analysis_result.get("tone"):
                                st.markdown(f"**Tone:** {tone}")
                            if triggers := analysis_result.get("potential_triggers", []):
                                st.markdown("**Potential triggers:**")
                                for trigger in triggers:
                                    st.markdown(f"• {trigger}")
                        else:
                            st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                        st.markdown(f"**Reframed:** {reframed}")
                        st.code(reframed, language="text")
        else:
            # Show all conversations if none selected
            for entry in history_data:
                st.markdown(f"**[{entry['timestamp']}] {entry['context']}**")
                st.markdown(f"**Original:** {entry['original']}")
                st.markdown(f"**Sentiment:** {entry['sentiment'].title()}")
                st.markdown(f"**Reframed:** {entry['reframed']}")
                st.markdown("---")
    
    else:
        st.info("No conversation history yet. Analyze a message to start!")
    
    # Download button for local storage
    import json
    history_json = json.dumps(st.session_state.history, indent=2)
    st.download_button(
        label="📥 Save History to Your Device",
        data=history_json,
        file_name=f"third_voice_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        help="Downloads your conversation history to your phone or computer’s Downloads folder for privacy."
    )
