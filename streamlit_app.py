streamlit_app.py

MVP Version of The Third Voice – Ready for GitHub deployment

import streamlit as st import google.generativeai as genai import json from typing import Dict import uuid import datetime

--- Configuration ---

st.set_page_config( page_title="The Third Voice", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded" )

--- Custom Styling ---

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
</style>""", unsafe_allow_html=True)

--- Load API Key from Streamlit Secrets ---

api_key = st.secrets.get("GEMINI_API_KEY") genai.configure(api_key=api_key)

--- Gemini Setup ---

model = genai.GenerativeModel("gemini-1.5-flash")

--- App Header ---

st.markdown("""

<div class="main-header">
  <h1>🎙️ The Third Voice</h1>
  <h4>Your AI Co-Mediator for Emotionally Intelligent Messaging</h4>
</div>
""", unsafe_allow_html=True)--- Tabs ---

tab1, tab2 = st.tabs(["💬 Message Coach", "🧠 Emotional Translator"])

--- Tab 1: Message Coach ---

with tab1: st.markdown("### Draft or paste a message to reframe it supportively.") message_input = st.text_area("📩 Your message:", height=150) context = st.selectbox("🧭 Who is this message for?", ["general", "romantic", "coparenting", "workplace"])

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
            st.markdown("**Suggested Version:**")
            st.markdown(f'<div class="ai-response">{response.text.strip()}</div>', unsafe_allow_html=True)
            st.code(response.text.strip())
        except Exception as e:
            st.error(f"Error: {str(e)}")

--- Tab 2: Emotional Translator ---

with tab2: st.markdown("### Paste a received message to understand its emotional subtext.") received_input = st.text_area("📨 Message you received:", height=120)

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
            st.markdown(f'<div class="ai-response">{response.text.strip()}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")

--- Footer ---

st.caption("© 2025 The Third Voice | Built with 💜 in detention by Predrag Mirkovic")

