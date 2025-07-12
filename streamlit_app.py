import streamlit as st
import google.generativeai as genai
import json
import time
from typing import Dict, List

# --- Configuration and Setup ---

# Page configuration
st.set_page_config(
    page_title="The Third Voice",
    page_icon="🎙️", # Using a common microphone emoji
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
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
    
    .feature-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: #f9f9f9;
    }
    
    .ai-response {
        background: #f0f8ff;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .emotion-card {
        background: #e8f5e8;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
    }
    
    .sentiment-positive {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    
    .sentiment-negative {
        background: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    
    .sentiment-neutral {
        background: #d1ecf1;
        color: #0c5460;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

class GeminiMessageCoach:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.model = None # Initialize as None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                st.error(f"Failed to configure Gemini API: {e}. Please check your key.")
                self.api_key = None # Invalidate API key if configuration fails

    def _get_gemini_model(self):
        """Helper to check if model is configured"""
        if not self.model:
            st.error("Gemini API key not configured or failed to initialize.")
            return None
        return self.model

    def analyze_message(self, message: str) -> Dict:
        """Analyze message sentiment and emotions using Gemini"""
        model = self._get_gemini_model()
        if not model:
            return {"success": False, "error": "API key not configured or model failed to initialize."}

        try:
            prompt = f"""
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

            # Try to parse JSON from response
            try:
                result = json.loads(response.text)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, extract key info from text as a fallback
                text = response.text.lower()
                sentiment = "negative" if "negative" in text or "angry" in text or "frustrated" in text else \
                            "positive" if "positive" in text or "happy" in text or "joy" in text else \
                            "neutral"

                return {
                    "success": True,
                    "sentiment": sentiment,
                    "confidence": 0.8, # Default confidence for fallback
                    "primary_emotion": "mixed",
                    "emotions": [],
                    "tone": "Analysis completed (fallback)",
                    "potential_triggers": [],
                    "raw_response": response.text
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def reframe_message(self, message: str, context: str = "general") -> str:
        """Reframe message using Gemini"""
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

            Return only the reframed message, no explanations.
            """

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            return self._fallback_reframe(message, context)

    def _fallback_reframe(self, message: str, context: str) -> str:
        """Fallback reframing when Gemini is unavailable or errors"""
        reframed = message.lower()

        # Basic replacements
        reframed = reframed.replace("you always", "I've noticed")
        reframed = reframed.replace("you never", "it would help if")
        reframed = reframed.replace("you", "I feel") # This is a very broad replacement
        reframed = reframed.replace("always", "sometimes")
        reframed = reframed.replace("never", "rarely")

        if context == "coparenting":
            return f"Hi, I wanted to discuss something about our child. {reframed.capitalize()} Can we find a solution that works for everyone?"
        elif context == "romantic":
            return f"Hey love, I wanted to share something that's been on my mind. {reframed.capitalize()} I care about us and want to work through this together. ❤️"
        elif context == "workplace":
            return f"I wanted to discuss something with you. {reframed.capitalize()} I'd appreciate your thoughts on how we can improve this situation."
        else:
            return f"I hope you're doing well. I wanted to discuss something: {reframed.capitalize()} I'd love to hear your thoughts on this."

    def emotional_translation(self, message: str) -> str:
        """Translate the emotional subtext of a message"""
        model = self._get_gemini_model()
        if not model:
            return "API not configured or model failed to initialize. Please add your Gemini API key."

        try:
            prompt = f"""
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

# --- Streamlit App Layout ---

# Initialize session state
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""

# Initialize AI Coach (using st.cache_resource for efficiency)
@st.cache_resource
def get_ai_coach(api_key):
    return GeminiMessageCoach(api_key)

# Header
st.markdown(f"""
<div class="main-header">
    <h1>🎙️ The Third Voice</h1>
    <h3>Your AI co-mediator for emotionally intelligent communication</h3>
    <p><i>Built in detention, with a phone, for life's hardest moments.</i></p>
    <p>⚡ <strong>Powered by Google Gemini Flash</strong></p>
</div>
""", unsafe_allow_html=True)

# API Key Configuration
with st.expander("🔑 Configure Google Gemini API", expanded=not st.session_state.gemini_api_key):
    st.markdown("**Get your free API key from:** [Google AI Studio](https://aistudio.google.com/app/apikey)")

    api_key_input = st.text_input(
        "Enter your Gemini API key:",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Your API key is stored only in your browser session"
    )

    if st.button("Save API Key"):
        st.session_state.gemini_api_key = api_key_input
        st.success("API key saved! You can now use all AI features.")
        st.rerun()

# Initialize AI coach with current API key
ai_coach = get_ai_coach(st.session_state.gemini_api_key)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 AI Message Coach", "🗣️ Emotional Translator", "🤖 AI Models", "💡 About"])

with tab1:
    st.markdown("### AI-Powered Message Coaching")
    st.markdown("Real AI analysis of your message tone, emotions, and suggestions for improvement.")

    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please configure your Gemini API key above to use AI features.")

    col1, col2 = st.columns([1, 1])

    with col1:
        message_input = st.text_area(
            "Your message draft:",
            placeholder="Type the message you want to send...",
            height=150,
            key="message_input"
        )

        context = st.selectbox(
            "Context:",
            ["general", "romantic", "coparenting", "workplace"],
            index=0
        )

        if st.button("⚡ AI Analysis & Reframe", type="primary"):
            if message_input.strip():
                if not st.session_state.gemini_api_key:
                    st.error("Please configure your Gemini API key first.")
                else:
                    with st.spinner("⚡ AI is analyzing your message..."):
                        st.session_state.usage_count += 1

                        # Get AI analysis
                        analysis_result = ai_coach.analyze_message(message_input)

                        with col2:
                            st.markdown("#### ⚡ AI Analysis Results")

                            if analysis_result.get("success"):
                                sentiment = analysis_result.get("sentiment", "neutral")
                                confidence = analysis_result.get("confidence", 0.5)

                                # Display sentiment with styling
                                if sentiment == "negative":
                                    st.markdown(f'<div class="sentiment-negative">⚠️ Negative sentiment detected ({confidence:.1%} confidence)</div>', unsafe_allow_html=True)
                                elif sentiment == "positive":
                                    st.markdown(f'<div class="sentiment-positive">✅ Positive sentiment ({confidence:.1%} confidence)</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="sentiment-neutral">⚖️ Neutral sentiment ({confidence:.1%} confidence)</div>', unsafe_allow_html=True)

                                # Primary emotion
                                primary_emotion = analysis_result.get("primary_emotion", "mixed")
                                st.markdown(f"**Primary emotion:** {primary_emotion.title()}")

                                # Tone
                                tone = analysis_result.get("tone", "")
                                if tone:
                                    st.markdown(f"**Tone:** {tone}")

                                # Potential triggers
                                triggers = analysis_result.get("potential_triggers", [])
                                if triggers:
                                    st.markdown("**Potential triggers:**")
                                    for trigger in triggers:
                                        st.markdown(f"• {trigger}") # Using standard bullet

                                # Raw response if available
                                if "raw_response" in analysis_result:
                                    with st.expander("📄 Full AI Analysis"):
                                        st.text(analysis_result["raw_response"])

                            else:
                                st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")

                            # AI-Generated Reframe
                            st.markdown("#### ✨ AI-Suggested Reframe")
                            reframed = ai_coach.reframe_message(message_input, context)

                            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                            st.markdown(reframed)
                            st.markdown('</div>', unsafe_allow_html=True)

                            # Streamlit offers a copy button for code blocks naturally
                            st.code(reframed, language="text") # Specify language or None

            else:
                st.warning("Please enter a message to analyze.")

with tab2:
    st.markdown("### AI Emotional Translation")
    st.markdown("Let AI help you understand the emotional undertones of messages you receive.")

    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please configure your Gemini API key above to use AI features.")

    received_message = st.text_area(
        "Message you received:",
        placeholder="Paste the message you're trying to understand...",
        height=100
    )

    if st.button("⚡ AI Translate", type="primary"):
        if received_message.strip():
            if not st.session_state.gemini_api_key:
                st.error("Please configure your Gemini API key first.")
            else:
                with st.spinner("⚡ AI is analyzing the emotional subtext..."):
                    st.session_state.usage_count += 1

                    translation = ai_coach.emotional_translation(received_message)

                    st.markdown("#### 🗣️ AI Emotional Translation")
                    st.markdown(f"**Original message:** \"{received_message}\"")

                    st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                    st.markdown(translation)
                    st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.warning("Please enter a message to translate.")

with tab3:
    st.markdown("### 🤖 AI Models Powering The Third Voice")
    st.markdown("We use Google Gemini Flash for advanced natural language understanding:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎙️ Google Gemini Flash")
        st.markdown("**Model:** `gemini-1.5-flash`")
        st.markdown("- Advanced sentiment and emotion analysis")
        st.markdown("- Context-aware message reframing")
        st.markdown("- Emotional translation and interpretation")
        st.markdown("- Multi-context understanding")

        st.markdown("#### 🔑 API Configuration")
        st.markdown("- **Free tier:** 15 requests per minute")
        st.markdown("- **Rate limits:** 1,500 requests per day")
        st.markdown("- **Cost:** Free up to quota limits")

    with col2:
        st.markdown("#### ✅ Why Google Gemini?")
        st.markdown("- **Advanced reasoning** - better context understanding")
        st.markdown("- **Reliable API** - consistent performance")
        st.markdown("- **Free tier** - generous usage limits")
        st.markdown("- **Fast responses** - optimized for real-time use")

        st.markdown("#### ✨ Test the AI")
        if st.session_state.gemini_api_key:
            test_message = st.text_input("Test message:", placeholder="Type a message to test...")

            if st.button("⚡ Test AI Analysis") and test_message:
                with st.spinner("Testing..."):
                    result = ai_coach.analyze_message(test_message)

                    if result.get("success"):
                        st.success(f"Sentiment: {result.get('sentiment', 'unknown').title()}")
                        st.info(f"Primary emotion: {result.get('primary_emotion', 'unknown').title()}")
                        st.markdown(f"**Tone:** {result.get('tone', 'Not specified')}")
                    else:
                        st.error(f"Test failed: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Configure your API key first to test the AI.")

with tab4:
    st.markdown("## About The Third Voice")

    st.markdown("""
    The Third Voice was born from a deeply personal crisis – miscommunication during detention – 
    and emerged as a digital co-mediator to help people communicate calmly and constructively 
    in emotionally charged relationships.
    """)

    st.markdown("### 💡 Why it matters:")
    st.markdown("""
    - **Miscommunication**—not lack of care—often breaks relationships
    - **People text when emotional**, leading to misfires
    - **Therapy is slow/expensive**
    - **Everyone texts**—no one has a coach in their pocket
    """)

    st.markdown("### ⚡ Powered by Google Gemini")
    st.markdown("""
    - **Advanced AI** from Google's latest models
    - **Context-aware** analysis and reframing
    - **Privacy-focused** - your data stays with Google's secure API
    - **Free tier** available for personal use
    """)

    st.markdown("### 🌐 Connect with us:")
    st.markdown("""
    - **Website:** [TheThirdVoice.ai](https://TheThirdVoice.ai)
    - **Email:** hello@TheThirdVoice.ai
    - **Hashtag:** #TheThirdVoice
    - **Founder:** Predrag Mirkovic
    """)

    st.markdown("### 📊 Your Usage Stats:")
    st.markdown(f"- **AI requests this session:** {st.session_state.usage_count}")
    st.markdown(f"- **API configured:** {'✅ Yes' if st.session_state.gemini_api_key else '❌ No'}")

# Footer
st.markdown("---")
st.markdown("© 2025 The Third Voice | Built with ❤️ and ⚡ Google Gemini | [Visit TheThirdVoice.ai](https://TheThirdVoice.ai)")

# Sidebar
st.sidebar.markdown("### 📊 AI Status")
st.sidebar.markdown(f"**API Key:** {'✅ Configured' if st.session_state.gemini_api_key else '❌ Not configured'}")
st.sidebar.markdown(f"**Session uses:** {st.session_state.usage_count}")
st.sidebar.markdown("**Model:** Google Gemini Flash")

if st.session_state.gemini_api_key:
    st.sidebar.success("✅ AI Ready!")
else:
    st.sidebar.error("❌ Configure API key")

st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("💡 Try different contexts for better results")
            
