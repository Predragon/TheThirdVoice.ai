streamlit_app.py

import streamlit as st from components.message_coach import message_coach_tab from components.emotional_translator import emotional_translator_tab from components.header_footer import render_header, render_footer from styles.custom_css import inject_custom_css from config.settings import model

Page config

st.set_page_config( page_title="The Third Voice", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded" )

Styling

inject_custom_css()

Header

render_header()

Tabs

tab1, tab2 = st.tabs(["💬 Message Coach", "🧠 Emotional Translator"])

with tab1: message_coach_tab(model)

with tab2: emotional_translator_tab(model)

Footer

render_footer()

