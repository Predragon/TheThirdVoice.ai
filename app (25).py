"""
Third Voice - Streamlined Efficient Version
Removed copy button, added history management, added coparenting context
"""

import streamlit as st
import requests
import json
from datetime import datetime
import base64

# ===== Configuration =====
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = st.secrets.get("OPENROUTER_API_KEY")

CONTEXTS = {
    "general": {
        "color": "#5D9BFF", 
        "icon": "💙",
        "description": "Everyday conversations and general communication"
    },
    "romantic": {
        "color": "#FF7EB9", 
        "icon": "❤️",
        "description": "Personal relationships and intimate conversations"
    },
    "workplace": {
        "color": "#6EE7B7", 
        "icon": "💼",
        "description": "Professional communication and work-related messages"
    },
    "family": {
        "color": "#FFB347", 
        "icon": "👨‍👩‍👧‍👦",
        "description": "Family conversations and sensitive discussions"
    },
    "coparenting": {
        "color": "#9B59B6", 
        "icon": "👶",
        "description": "Co-parenting communication focused on child welfare"
    }
}

# ===== Streamlined UI Setup =====
st.set_page_config(
    page_title="Third Voice - Message Helper",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def apply_efficient_styles():
    st.markdown("""
    <style>
    /* Streamlined mobile-first design */
    div.stTextArea > textarea {
        font-size: 16px !important;
        min-height: 120px !important;
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 16px !important;
    }
    
    div.stTextArea > textarea:focus {
        border-color: #5D9BFF !important;
        box-shadow: 0 0 0 3px rgba(93, 155, 255, 0.1) !important;
    }
    
    div.stButton > button {
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        min-height: 48px !important;
    }
    
    .result-container {
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 2px 16px rgba(0,0,0,0.1);
        background: white;
    }
    
    .analysis-result {
        border-left: 4px solid #5D9BFF;
        background: linear-gradient(135deg, #f8fbff 0%, #e8f4ff 100%);
    }
    
    .improvement-result {
        border-left: 4px solid #10B981;
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }
    
    .selectable-text {
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        background: #f9fafb;
        font-family: inherit;
        line-height: 1.6;
        user-select: text;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
    }
    
    .char-counter {
        font-size: 12px;
        color: #6b7280;
        text-align: right;
        margin-top: 4px;
    }
    
    .char-counter.warning { color: #f59e0b; }
    .char-counter.error { color: #ef4444; }
    
    .help-icon {
        display: inline-block;
        margin-left: 4px;
        color: #6b7280;
        cursor: help;
        font-size: 12px;
    }
    
    @media (max-width: 768px) {
        div.stButton > button {
            width: 100% !important;
            margin-bottom: 8px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ===== Efficient Session State =====
def init_state():
    defaults = {
        'analyze_clicked': False,
        'coach_clicked': False,
        'selected_context': 'general',
        'message_history': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_actions():
    st.session_state.analyze_clicked = False
    st.session_state.coach_clicked = False

# ===== History Management =====
def add_to_history(original, result, action, context):
    item = {
        'timestamp': datetime.now().isoformat(),
        'original': original,
        'result': result,
        'action': action,
        'context': context
    }
    st.session_state.message_history.insert(0, item)
    if len(st.session_state.message_history) > 50:
        st.session_state.message_history = st.session_state.message_history[:50]

def download_history():
    if not st.session_state.message_history:
        return None
    
    history_data = {
        'exported_date': datetime.now().isoformat(),
        'total_items': len(st.session_state.message_history),
        'history': st.session_state.message_history
    }
    
    json_str = json.dumps(history_data, indent=2, ensure_ascii=False)
    b64 = base64.b64encode(json_str.encode()).decode()
    
    filename = f"third_voice_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return f'<a href="data:application/json;base64,{b64}" download="{filename}" style="text-decoration:none"><button style="background:#10B981;color:white;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;">📥 Download History</button></a>'

def upload_history(uploaded_file):
    try:
        history_data = json.load(uploaded_file)
        if 'history' in history_data and isinstance(history_data['history'], list):
            st.session_state.message_history = history_data['history']
            return True, f"✅ Loaded {len(history_data['history'])} items"
        else:
            return False, "❌ Invalid file format"
    except Exception as e:
        return False, f"❌ Error loading file: {str(e)}"

# ===== API Functions =====
def get_system_prompt(action, context):
    prompts = {
        'analyze': {
            'general': "Analyze the emotional tone, clarity, and potential impact of this message. Provide constructive insights.",
            'romantic': "Analyze this romantic message for emotional tone, intimacy level, and how your partner might interpret it.",
            'workplace': "Analyze this professional message for tone, clarity, workplace appropriateness, and potential misinterpretations.",
            'family': "Analyze this family message for emotional sensitivity, generational considerations, and family dynamics impact.",
            'coparenting': "Analyze this co-parenting message focusing on child welfare, neutral tone, and constructive communication."
        },
        'improve': {
            'general': "Improve this message for better clarity, kindness, and effectiveness while maintaining the original intent.",
            'romantic': "Enhance this romantic message to be more loving, clear, and emotionally connecting while preserving authenticity.",
            'workplace': "Improve this professional message for clarity, appropriate tone, and workplace effectiveness.",
            'family': "Enhance this family message to be more understanding, sensitive, and strengthen family relationships.",
            'coparenting': "Improve this co-parenting message to be child-focused, neutral, respectful, and solution-oriented."
        }
    }
    return prompts[action].get(context, prompts[action]['general'])

def call_api(message, action, context):
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "HTTP-Referer": "https://third-voice.streamlit.app",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {"role": "system", "content": get_system_prompt(action, context)},
                    {"role": "user", "content": f"Context: {context.capitalize()}\nMessage: {message}"}
                ],
                "max_tokens": 800,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"API Error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except Exception as e:
        return None, f"Error: {str(e)}"

# ===== Help Tooltips =====
def show_help_tooltip(button_type):
    help_text = {
        'analyze': "🔍 **Analyze Message**: Get insights into your message's emotional tone, clarity, and how others might interpret it. Perfect for understanding the impact before sending.",
        'improve': "✨ **Improve Message**: Get a refined version of your message that's clearer, kinder, and more effective while keeping your original meaning."
    }
    st.info(help_text.get(button_type, ""))

# ===== Main App =====
def main():
    init_state()
    apply_efficient_styles()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1f2937; font-size: 2.5rem; margin-bottom: 8px;">💬 Third Voice</h1>
        <p style="color: #6b7280; font-size: 1.1rem;">Your AI communication assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Context Selection
    st.markdown("### 🎯 Choose your context:")
    context_cols = st.columns(len(CONTEXTS))
    
    for i, (key, info) in enumerate(CONTEXTS.items()):
        with context_cols[i % len(CONTEXTS)]:
            if st.button(
                f"{info['icon']} {key.capitalize()}",
                key=f"context_{key}",
                use_container_width=True,
                type="primary" if st.session_state.selected_context == key else "secondary"
            ):
                st.session_state.selected_context = key
                reset_actions()
    
    # Context description
    selected_info = CONTEXTS[st.session_state.selected_context]
    st.markdown(f"""
    <div style="background: rgba(93, 155, 255, 0.1); border-radius: 8px; padding: 12px; margin: 16px 0;">
        <small style="color: #4b5563;"><strong>{selected_info['icon']} {st.session_state.selected_context.capitalize()}:</strong> {selected_info['description']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Message Input
    st.markdown("### ✍️ Your message:")
    user_input = st.text_area(
        "",
        placeholder="Type or paste your message here...",
        height=150,
        label_visibility="collapsed"
    )
    
    # Character counter
    char_count = len(user_input)
    counter_class = "error" if char_count > 2000 else "warning" if char_count > 1500 else ""
    st.markdown(f"""
    <div class="char-counter {counter_class}">
        {char_count}/2000 characters
    </div>
    """, unsafe_allow_html=True)
    
    # Action Buttons with Help
    st.markdown("### 🚀 Choose action:")
    button_cols = st.columns([1, 1, 2])
    
    with button_cols[0]:
        analyze_btn = st.button(
            "🔍 Analyze",
            use_container_width=True,
            disabled=char_count > 2000
        )
        if st.button("❓", key="help_analyze", help="Click for help"):
            show_help_tooltip('analyze')
        
        if analyze_btn:
            st.session_state.analyze_clicked = True
            st.session_state.coach_clicked = False
    
    with button_cols[1]:
        improve_btn = st.button(
            "✨ Improve",
            type="primary",
            use_container_width=True,
            disabled=char_count > 2000
        )
        if st.button("❓", key="help_improve", help="Click for help"):
            show_help_tooltip('improve')
            
        if improve_btn:
            st.session_state.coach_clicked = True
            st.session_state.analyze_clicked = False
    
    # Process Actions
    if (st.session_state.analyze_clicked or st.session_state.coach_clicked) and user_input.strip():
        action = "analyze" if st.session_state.analyze_clicked else "improve"
        
        with st.spinner("🤔 AI is thinking..."):
            result, error = call_api(user_input, action, st.session_state.selected_context)
        
        if error:
            st.error(f"❌ {error}")
            if st.button("🔄 Try Again", use_container_width=True):
                reset_actions()
                st.rerun()
        else:
            add_to_history(user_input, result, action, st.session_state.selected_context)
            
            # Display result
            result_class = "analysis-result" if action == "analyze" else "improvement-result"
            action_icon = "🔍" if action == "analyze" else "✨"
            action_title = "Analysis" if action == "analyze" else "Improved Message"
            
            st.markdown(f"""
            <div class="result-container {result_class}">
                <h4 style="margin-top: 0; color: #1f2937;">{action_icon} {action_title}</h4>
                <div style="line-height: 1.6; color: #374151;">{result}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Selectable text for easy copying
            st.markdown("### 📱 Tap and hold to select text:")
            st.markdown(f"""
            <div class="selectable-text">
                {result}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 New Analysis", use_container_width=True):
                reset_actions()
                st.rerun()
    
    elif (st.session_state.analyze_clicked or st.session_state.coach_clicked) and not user_input.strip():
        st.warning("⚠️ Please enter a message to analyze or improve.")
        reset_actions()
    
    # History Management Section
    st.markdown("---")
    st.markdown("### 📚 History Management")
    
    hist_cols = st.columns([1, 1, 2])
    
    with hist_cols[0]:
        # Download History
        if st.session_state.message_history:
            download_link = download_history()
            if download_link:
                st.markdown(download_link, unsafe_allow_html=True)
        else:
            st.button("📥 Download", disabled=True, help="No history to download")
    
    with hist_cols[1]:
        # Upload History
        if st.button("📤 Upload"):
            st.session_state.show_upload = not getattr(st.session_state, 'show_upload', False)
    
    # Upload interface
    if getattr(st.session_state, 'show_upload', False):
        uploaded_file = st.file_uploader(
            "Choose history file",
            type=['json'],
            key="history_upload"
        )
        
        if uploaded_file:
            success, message = upload_history(uploaded_file)
            if success:
                st.success(message)
                st.session_state.show_upload = False
                st.rerun()
            else:
                st.error(message)
    
    # Show History
    if st.session_state.message_history:
        with st.expander(f"📖 Recent History ({len(st.session_state.message_history)} items)", expanded=False):
            for i, item in enumerate(st.session_state.message_history[:10]):
                action_icon = "🔍" if item['action'] == "analyze" else "✨"
                context_info = CONTEXTS[item['context']]
                timestamp = datetime.fromisoformat(item['timestamp']).strftime("%m/%d %H:%M")
                
                st.markdown(f"""
                <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin: 8px 0; background: #f9fafb;">
                    <div style="font-size: 14px; color: #6b7280; margin-bottom: 8px;">
                        {action_icon} {timestamp} - {context_info['icon']} {item['context'].capitalize()}
                    </div>
                    <div style="font-size: 13px; color: #374151; margin-bottom: 8px;">
                        <strong>Original:</strong> {item['original'][:100]}{'...' if len(item['original']) > 100 else ''}
                    </div>
                    <div style="font-size: 13px; color: #374151;">
                        <strong>Result:</strong> {item['result'][:150]}{'...' if len(item['result']) > 150 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 14px; padding: 20px 0;">
        💡 <strong>Pro tip:</strong> Use the help buttons (❓) to learn more about each feature!<br>
        Made with ❤️ for better human connections
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
