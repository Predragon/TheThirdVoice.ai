"""
Third Voice - Enhanced Workflow Version
Improved UX, performance, and functionality
"""

import streamlit as st
import requests
from streamlit.components.v1 import html
import time
import json
from datetime import datetime

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
    }
}

# ===== Enhanced Mobile UI Setup =====
st.set_page_config(
    page_title="Third Voice - Message Helper",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def apply_enhanced_styles():
    st.markdown(f"""
    <style>
    /* Enhanced mobile-first design */
    .main-container {{
        max-width: 100%;
        padding: 1rem;
    }}
    
    /* Input improvements */
    div.stTextArea > textarea {{
        font-size: 16px !important;
        min-height: 120px !important;
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 16px !important;
        transition: border-color 0.3s ease;
    }}
    
    div.stTextArea > textarea:focus {{
        border-color: #5D9BFF !important;
        box-shadow: 0 0 0 3px rgba(93, 155, 255, 0.1) !important;
    }}
    
    /* Button enhancements */
    div.stButton > button {{
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        min-height: 48px !important;
    }}
    
    div.stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }}
    
    /* Context selector styling */
    .context-card {{
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        background: white;
    }}
    
    .context-card:hover {{
        border-color: #5D9BFF;
        box-shadow: 0 2px 8px rgba(93, 155, 255, 0.1);
    }}
    
    .context-card.selected {{
        border-color: #5D9BFF;
        background: rgba(93, 155, 255, 0.05);
    }}
    
    /* Results styling */
    .result-container {{
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 2px 16px rgba(0,0,0,0.1);
        background: white;
    }}
    
    .analysis-result {{
        border-left: 4px solid #5D9BFF;
        background: linear-gradient(135deg, #f8fbff 0%, #e8f4ff 100%);
    }}
    
    .improvement-result {{
        border-left: 4px solid #10B981;
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }}
    
    /* Copy functionality */
    .copy-section {{
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        background: #f9fafb;
        position: relative;
    }}
    
    .copy-toast {{
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        padding: 12px 24px;
        background: #10B981;
        color: white;
        border-radius: 24px;
        z-index: 9999;
        font-weight: 600;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
    }}
    
    /* Loading spinner */
    .loading-container {{
        text-align: center;
        padding: 40px;
    }}
    
    /* Character counter */
    .char-counter {{
        font-size: 12px;
        color: #6b7280;
        text-align: right;
        margin-top: 4px;
    }}
    
    .char-counter.warning {{
        color: #f59e0b;
    }}
    
    .char-counter.error {{
        color: #ef4444;
    }}
    
    /* History section */
    .history-item {{
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        background: #f9fafb;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .history-item:hover {{
        background: #f3f4f6;
        border-color: #5D9BFF;
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .main-container {{
            padding: 0.5rem;
        }}
        
        div.stButton > button {{
            width: 100% !important;
            margin-bottom: 8px !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

def enhanced_copy_to_clipboard(text, success_message="✅ Copied to clipboard!"):
    """Enhanced copy function with better feedback"""
    # Clean text for JavaScript
    clean_text = text.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    
    html(f"""
    <script>
    function copyText() {{
        const textToCopy = `{clean_text}`;
        
        // Create temporary element
        const tempElement = document.createElement('textarea');
        tempElement.value = textToCopy;
        tempElement.style.position = 'fixed';
        tempElement.style.opacity = '0';
        document.body.appendChild(tempElement);
        
        try {{
            // Try modern clipboard API first
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(textToCopy).then(() => {{
                    showToast('{success_message}');
                }}).catch(() => {{
                    // Fallback to legacy method
                    tempElement.select();
                    document.execCommand('copy');
                    showToast('{success_message}');
                }});
            }} else {{
                // Legacy method
                tempElement.select();
                tempElement.setSelectionRange(0, 99999); // For mobile devices
                document.execCommand('copy');
                showToast('{success_message}');
            }}
        }} catch (err) {{
            console.error('Copy failed:', err);
            showToast('❌ Copy failed - please select and copy manually');
        }} finally {{
            document.body.removeChild(tempElement);
        }}
    }}
    
    function showToast(message) {{
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.copy-toast');
        existingToasts.forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = 'copy-toast';
        toast.innerHTML = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {{
            if (toast.parentNode) {{
                toast.remove();
            }}
        }}, 3000);
    }}
    
    // Auto-copy when script loads
    copyText();
    </script>
    """, height=0)

# ===== Session State Management =====
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'analyze_clicked': False,
        'coach_clicked': False,
        'current_result': None,
        'current_action': None,
        'message_history': [],
        'selected_context': 'general',
        'show_history': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def reset_action_state():
    """Reset button click states"""
    st.session_state.analyze_clicked = False
    st.session_state.coach_clicked = False

def add_to_history(original_message, result, action, context):
    """Add interaction to history"""
    history_item = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'original': original_message[:100] + "..." if len(original_message) > 100 else original_message,
        'result': result,
        'action': action,
        'context': context
    }
    
    # Keep only last 10 items
    if len(st.session_state.message_history) >= 10:
        st.session_state.message_history.pop(0)
    
    st.session_state.message_history.append(history_item)

# ===== API Functions =====
def get_system_prompt(action, context):
    """Generate contextual system prompts"""
    base_prompts = {
        'analyze': {
            'general': "Analyze the emotional tone, clarity, and potential impact of this message. Provide constructive insights about how it might be received.",
            'romantic': "Analyze this romantic message for emotional tone, intimacy level, and potential impact. Consider how your partner might interpret and feel about it.",
            'workplace': "Analyze this professional message for tone, clarity, and workplace appropriateness. Consider hierarchy, formality, and potential misinterpretations.",
            'family': "Analyze this family message for emotional sensitivity, generational considerations, and potential family dynamics impact."
        },
        'improve': {
            'general': "Improve this message for better clarity, kindness, and effectiveness while maintaining the original intent and tone.",
            'romantic': "Enhance this romantic message to be more loving, clear, and emotionally connecting while preserving authenticity.",
            'workplace': "Improve this professional message for clarity, appropriate tone, and workplace effectiveness while maintaining professionalism.",
            'family': "Enhance this family message to be more understanding, sensitive, and likely to strengthen family relationships."
        }
    }
    
    return base_prompts[action].get(context, base_prompts[action]['general'])

def call_api(message, action, context):
    """Enhanced API call with better error handling"""
    try:
        system_prompt = get_system_prompt(action, context)
        
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
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context.capitalize()}\nMessage: {message}"}
                ],
                "max_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.9
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            return result, None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check your internet connection."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# ===== Main App Interface =====
def main():
    init_session_state()
    apply_enhanced_styles()
    
    # App Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1f2937; font-size: 2.5rem; margin-bottom: 8px;">💬 Third Voice</h1>
        <p style="color: #6b7280; font-size: 1.1rem;">Your AI communication assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Context Selection
    st.markdown("### 🎯 Choose your context:")
    
    context_cols = st.columns(2)
    for i, (key, info) in enumerate(CONTEXTS.items()):
        with context_cols[i % 2]:
            if st.button(
                f"{info['icon']} {key.capitalize()}",
                key=f"context_{key}",
                use_container_width=True,
                type="primary" if st.session_state.selected_context == key else "secondary"
            ):
                st.session_state.selected_context = key
                reset_action_state()
    
    # Show selected context description
    selected_info = CONTEXTS[st.session_state.selected_context]
    st.markdown(f"""
    <div style="background: rgba(93, 155, 255, 0.1); border-radius: 8px; padding: 12px; margin: 16px 0;">
        <small style="color: #4b5563;"><strong>{selected_info['icon']} {st.session_state.selected_context.capitalize()}:</strong> {selected_info['description']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Message Input Section
    st.markdown("### ✍️ Your message:")
    user_input = st.text_area(
        "",
        placeholder="Type or paste your message here...",
        height=150,
        key="message_input",
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
    
    # Action Buttons
    st.markdown("### 🚀 Choose action:")
    button_cols = st.columns(2)
    
    with button_cols[0]:
        analyze_btn = st.button(
            "🔍 Analyze Message",
            use_container_width=True,
            disabled=char_count > 2000
        )
        if analyze_btn:
            st.session_state.analyze_clicked = True
            st.session_state.coach_clicked = False
    
    with button_cols[1]:
        improve_btn = st.button(
            "✨ Improve Message",
            type="primary",
            use_container_width=True,
            disabled=char_count > 2000
        )
        if improve_btn:
            st.session_state.coach_clicked = True
            st.session_state.analyze_clicked = False
    
    # Process Actions
    if (st.session_state.analyze_clicked or st.session_state.coach_clicked) and user_input.strip():
        action = "analyze" if st.session_state.analyze_clicked else "improve"
        
        with st.spinner("🤔 AI is thinking..."):
            # Progress bar for better UX
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)  # Small delay for visual effect
                progress_bar.progress(i + 1)
            
            result, error = call_api(user_input, action, st.session_state.selected_context)
            progress_bar.empty()
        
        if error:
            st.error(f"❌ {error}")
            if st.button("🔄 Try Again", use_container_width=True):
                reset_action_state()
                st.rerun()
        else:
            # Store result
            st.session_state.current_result = result
            st.session_state.current_action = action
            
            # Add to history
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
            
            # Copy Section
            st.markdown("### 📋 Copy Result")
            copy_cols = st.columns([1, 2])
            
            with copy_cols[0]:
                if st.button("📋 Copy", use_container_width=True, key="copy_main"):
                    enhanced_copy_to_clipboard(result)
            
            with copy_cols[1]:
                if st.button("🔄 New Analysis", use_container_width=True, key="new_analysis"):
                    reset_action_state()
                    st.rerun()
            
            # Selectable text fallback
            st.markdown(f"""
            <div class="copy-section">
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 8px;">
                    📱 Mobile users: Press and hold to select text below
                </div>
                <div style="font-family: inherit; line-height: 1.5;">{result}</div>
            </div>
            """, unsafe_allow_html=True)
    
    elif (st.session_state.analyze_clicked or st.session_state.coach_clicked) and not user_input.strip():
        st.warning("⚠️ Please enter a message to analyze or improve.")
        reset_action_state()
    
    # History Section
    if st.session_state.message_history:
        st.markdown("---")
        history_expander = st.expander(f"📚 Recent History ({len(st.session_state.message_history)} items)", expanded=False)
        
        with history_expander:
            for i, item in enumerate(reversed(st.session_state.message_history)):
                action_icon = "🔍" if item['action'] == "analyze" else "✨"
                context_info = CONTEXTS[item['context']]
                
                if st.button(
                    f"{action_icon} {item['timestamp']} - {context_info['icon']} {item['context'].capitalize()}",
                    key=f"history_{i}",
                    use_container_width=True
                ):
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin: 8px 0;">
                        <strong>Original:</strong> {item['original']}<br><br>
                        <strong>Result:</strong> {item['result']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("📋 Copy This Result", key=f"copy_history_{i}", use_container_width=True):
                        enhanced_copy_to_clipboard(item['result'])
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 14px; padding: 20px 0;">
        💡 <strong>Pro tip:</strong> Be specific about your communication goals for better results!<br>
        Made with ❤️ for better human connections
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
