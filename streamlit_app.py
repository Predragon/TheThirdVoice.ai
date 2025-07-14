import streamlit as st
import google.generativeai as genai

# --- Page Setup ---
st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded")

# --- Custom Styling ---
st.markdown("""
<style>
.sidebar .sidebar-content { padding-top: 1rem; }
.main-header {
    text-align: center;
    background: linear-gradient(90deg, #667eea, #764ba2);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
}
.ai-response {
    background: #f0f8ff;
    border-left: 4px solid #4CAF50;
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# --- Load API Key from Streamlit Secrets ---
api_key = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# --- Gemini Setup ---
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Session State Setup for History ---
if "rewrite_history" not in st.session_state:
    st.session_state.rewrite_history = []
if "translation_history" not in st.session_state:
    st.session_state.translation_history = []

# --- App Header ---
st.markdown("""
<div class="main-header">
  <h1>🎙️ The Third Voice</h1>
  <h4>Your AI Co-Mediator for Emotionally Intelligent Messaging</h4>
</div>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2 = st.tabs(["💬 Message Coach", "🧠 Emotional Translator"])

# --- Tab 1: Message Coach ---
with tab1:
    st.markdown("### Draft or paste a message to reframe it supportively.")
    message_input = st.text_area("📩 Your message:", height=150)
    context = st.selectbox("🧭 Who is this message for?", ["general", "romantic", "coparenting", "workplace"])

    if st.button("💡 Analyze and Suggest Rewrite") and message_input.strip():
        with st.spinner("Analyzing message and generating reframed version..."):
            prompt = f"""
            Rewrite this message to sound more emotionally intelligent, constructive, and supportive.
            Context: {context}
            Original message: "{message_input}"
            Return only the improved message.
            """
            try:
                response = model.generate_content(prompt)
                improved = response.text.strip()
                st.session_state.rewrite_history.append(improved)
                st.markdown("**Suggested Version:**")
                st.markdown(f'<div class="ai-response">{improved}</div>', unsafe_allow_html=True)
                st.code(improved)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if st.session_state.rewrite_history:
        st.markdown("#### 🧾 Your Session Rewrite History:")
        for i, msg in enumerate(st.session_state.rewrite_history[::-1], 1):
            st.markdown(f'<div class="ai-response"><b>{i}.</b> {msg}</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Rewrite History"):
            st.session_state.rewrite_history.clear()

# --- Tab 2: Emotional Translator ---
with tab2:
    st.markdown("### Paste a received message to understand its emotional subtext.")
    received_input = st.text_area("📨 Message you received:", height=120)

    if st.button("🔍 Translate Emotional Meaning") and received_input.strip():
        with st.spinner("Reading between the lines..."):
            prompt = f"""
            Analyze this message for emotional subtext and intention.
            Answer:
            1. What emotions are likely behind this message?
            2. What might the sender actually mean or feel?
            3. How can the receiver best respond?
            Message: "{received_input}"
            """
            try:
                response = model.generate_content(prompt)
                insight = response.text.strip()
                st.session_state.translation_history.append(insight)
                st.markdown(f'<div class="ai-response">{insight}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if st.session_state.translation_history:
        st.markdown("#### 🧾 Your Session Emotional Insights:")
        for i, msg in enumerate(st.session_state.translation_history[::-1], 1):
            st.markdown(f'<div class="ai-response"><b>{i}.</b> {msg}</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Translation History"):
            st.session_state.translation_history.clear()

# --- Footer ---
st.caption("© 2025 The Third Voice | Built with 💜 in detention by Predrag Mirkovic")
