toimport streamlit as st
import google.generativeai as genai
import json
from typing import Dict, List
import uuid
import datetime
import re
from dataclasses import dataclass, asdict
from enum import Enum

# --- Configuration and Setup ---
st.set_page_config(
    page_title="The Third Voice",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Models ---
class RelationshipType(Enum):
    ROMANTIC = "romantic"
    COPARENTING = "coparenting"
    FAMILY = "family"
    FRIEND = "friend"
    COWORKER = "coworker"
    PROFESSIONAL = "professional"

class EmotionalRisk(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Relationship:
    id: str
    name: str
    type: RelationshipType
    notes: str = ""
    created_at: datetime.datetime = None
    last_interaction: datetime.datetime = None
    emotional_risk: EmotionalRisk = EmotionalRisk.LOW
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.datetime.now()
        if self.last_interaction is None:
            self.last_interaction = datetime.datetime.now()

@dataclass
class Message:
    id: str
    relationship_id: str
    content: str
    is_outgoing: bool
    timestamp: datetime.datetime
    ai_analysis: Dict = None
    reframed_version: str = ""
    emotional_flags: List[str] = None
    
    def __post_init__(self):
        if self.emotional_flags is None:
            self.emotional_flags = []

@dataclass
class Conversation:
    id: str
    relationship_id: str
    messages: List[Message]
    created_at: datetime.datetime
    title: str = ""
    
    def __post_init__(self):
        if not self.title:
            self.title = f"Conversation {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# --- Enhanced CSS (unchanged from provided code) ---
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .relationship-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .relationship-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    
    .relationship-card.active {
        border-left-color: #4CAF50;
        background: #f8fff8;
    }
    
    .risk-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .risk-low { background: #4CAF50; }
    .risk-moderate { background: #FF9800; }
    .risk-high { background: #f44336; }
    .risk-critical { background: #9C27B0; }
    
    .message-bubble {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 15px;
        position: relative;
    }
    
    .message-incoming {
        background: #f5f5f5;
        border-bottom-left-radius: 5px;
        margin-right: 20%;
    }
    
    .message-outgoing {
        background: #667eea;
        color: white;
        border-bottom-right-radius: 5px;
        margin-left: 20%;
    }
    
    .ai-analysis-card {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0f8ff 100%);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .emotional-flag {
        display: inline-block;
        background: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85em;
        margin: 0.25rem;
        border: 1px solid #ffeaa7;
    }
    
    .critical-flag {
        background: #f8d7da;
        color: #721c24;
        border-color: #f5c6cb;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .conversation-history {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        background: #fafafa;
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
    
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'relationships' not in st.session_state:
    st.session_state.relationships = {}
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'selected_relationship' not in st.session_state:
    st.session_state.selected_relationship = None
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0

# --- API Key Configuration ---
api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", "")
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = api_key_from_secrets

# --- Enhanced GeminiMessageCoach Class (unchanged from provided code) ---
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

    def analyze_message(self, message: str, relationship_context: str = "general") -> Dict:
        model = self._get_gemini_model()
        if not model:
            return {"success": False, "error": "API key not configured"}

        try:
            prompt = f"""
            Analyze this message for emotional content and communication risks in a {relationship_context} context.
            
            Message: "{message}"
            
            Return a JSON response with:
            1. sentiment: "positive", "negative", or "neutral"
            2. confidence: number 0.0-1.0
            3. primary_emotion: main emotion detected
            4. emotions: list of emotions with intensity scores
            5. tone: overall tone description
            6. potential_triggers: words/phrases that might cause negative reactions
            7. emotional_risk: "low", "moderate", "high", or "critical"
            8. communication_flags: specific issues (defensive, accusatory, dismissive, etc.)
            9. suggested_improvements: specific recommendations
            10. urgency_level: how quickly this needs attention (1-10)
            
            Focus on {relationship_context} relationship dynamics.
            Return only valid JSON.
            """
            
            response = model.generate_content(prompt)
            try:
                result = json.loads(response.text)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                return self._fallback_analysis(message)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _fallback_analysis(self, message: str) -> Dict:
        negative_words = ["hate", "never", "always", "terrible", "awful", "stupid", "idiot"]
        positive_words = ["love", "appreciate", "thank", "wonderful", "great", "amazing"]
        
        lower_msg = message.lower()
        neg_count = sum(1 for word in negative_words if word in lower_msg)
        pos_count = sum(1 for word in positive_words if word in lower_msg)
        
        if neg_count > pos_count:
            sentiment = "negative"
        elif pos_count > neg_count:
            sentiment = "positive"
        else:
            sentiment = "neutral"
            
        return {
            "success": True,
            "sentiment": sentiment,
            "confidence": 0.7,
            "primary_emotion": "mixed",
            "emotions": [],
            "tone": "Analyzed with fallback method",
            "potential_triggers": [],
            "emotional_risk": "moderate" if neg_count > 0 else "low",
            "communication_flags": [],
            "suggested_improvements": [],
            "urgency_level": 5
        }

    def reframe_message(self, message: str, relationship_type: str = "general") -> str:
        model = self._get_gemini_model()
        if not model:
            return self._fallback_reframe(message, relationship_type)

        try:
            context_guides = {
                "romantic": "Focus on love, partnership, and emotional connection. Use gentle, caring language.",
                "coparenting": "Prioritize child welfare. Use collaborative, solution-focused language.",
                "family": "Emphasize family bonds and respect. Use understanding, supportive language.",
                "friend": "Maintain friendship warmth while being honest. Use loyal, caring language.",
                "coworker": "Stay professional and constructive. Use respectful, solution-oriented language.",
                "professional": "Maintain professionalism. Use diplomatic, business-appropriate language."
            }
            
            prompt = f"""
            Rewrite this message for a {relationship_type} relationship to be more emotionally intelligent and constructive.
            
            Guidelines: {context_guides.get(relationship_type, "Use diplomatic, empathetic language")}
            
            Original: "{message}"
            
            Rules:
            1. Keep the core message intent
            2. Remove blame language ("you always", "you never")
            3. Use "I" statements when possible
            4. Add empathy and understanding
            5. Focus on solutions and collaboration
            6. Make it authentic and natural
            7. Reduce emotional intensity while maintaining sincerity
            
            Return only the reframed message.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return self._fallback_reframe(message, relationship_type)

    def _fallback_reframe(self, message: str, relationship_type: str) -> str:
        reframed = message.replace("you always", "I've noticed that sometimes")
        reframed = reframed.replace("you never", "it would help if we could")
        reframed = reframed.replace("You're wrong", "I see this differently")
        reframed = reframed.replace("That's stupid", "I don't understand that approach")
        
        if relationship_type == "coparenting":
            return f"For our child's wellbeing, I'd like to discuss: {reframed}"
        elif relationship_type == "romantic":
            return f"I care about us, and I wanted to share that {reframed}"
        else:
            return f"I'd like to discuss: {reframed}"

    def detect_crisis_signals(self, message: str) -> Dict:
        model = self._get_gemini_model()
        if not model:
            return {"is_crisis": False, "risk_level": "unknown"}

        try:
            prompt = f"""
            Analyze this message for crisis-level emotional content or dangerous communication patterns.
            
            Message: "{message}"
            
            Look for:
            - Threats or aggressive language
            - Self-harm indicators
            - Extreme emotional distress
            - Manipulative or controlling language
            - Escalation patterns
            
            Return JSON with:
            1. is_crisis: boolean
            2. risk_level: "low", "moderate", "high", "critical"
            3. crisis_indicators: list of specific concerns
            4. recommended_actions: what the user should do
            5. should_seek_help: boolean for professional intervention
            
            Return only valid JSON.
            """
            
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception:
            crisis_words = ["kill", "die", "suicide", "hurt", "weapon", "threat"]
            lower_msg = message.lower()
            is_crisis = any(word in lower_msg for word in crisis_words)
            
            return {
                "is_crisis": is_crisis,
                "risk_level": "high" if is_crisis else "low",
                "crisis_indicators": [word for word in crisis_words if word in lower_msg],
                "recommended_actions": ["Seek immediate professional help"] if is_crisis else [],
                "should_seek_help": is_crisis
            }

# --- Helper Functions ---
def save_relationship(relationship: Relationship):
    st.session_state.relationships[relationship.id] = relationship

def get_relationship(relationship_id: str) -> Relationship:
    return st.session_state.relationships.get(relationship_id)

def save_conversation(conversation: Conversation):
    st.session_state.conversations[conversation.id] = conversation

def get_conversations_for_relationship(relationship_id: str) -> List[Conversation]:
    return [conv for conv in st.session_state.conversations.values() 
            if conv.relationship_id == relationship_id]

def calculate_relationship_risk(relationship_id: str) -> EmotionalRisk:
    conversations = get_conversations_for_relationship(relationship_id)
    if not conversations:
        return EmotionalRisk.LOW
    
    recent_messages = []
    for conv in conversations[-5:]:  # Last 5 conversations
        recent_messages.extend(conv.messages[-10:])  # Last 10 messages each
    
    high_risk_count = sum(1 for msg in recent_messages 
                         if msg.ai_analysis and msg.ai_analysis.get('emotional_risk') in ['high', 'critical'])
    
    if high_risk_count > 5:
        return EmotionalRisk.CRITICAL
    elif high_risk_count > 2:
        return EmotionalRisk.HIGH
    elif high_risk_count > 0:
        return EmotionalRisk.MODERATE
    else:
        return EmotionalRisk.LOW

def get_relationship_stats(relationship_id: str) -> Dict:
    conversations = get_conversations_for_relationship(relationship_id)
    if not conversations:
        return {
            "total_messages": 0,
            "conversations": 0,
            "avg_sentiment": "neutral",
            "last_interaction": None
        }
    
    total_messages = sum(len(conv.messages) for conv in conversations)
    
    sentiments = []
    for conv in conversations:
        for msg in conv.messages:
            if msg.ai_analysis and msg.ai_analysis.get('sentiment'):
                sentiments.append(msg.ai_analysis['sentiment'])
    
    if sentiments:
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for sentiment in sentiments:
            sentiment_counts[sentiment] += 1
        avg_sentiment = max(sentiment_counts, key=sentiment_counts.get)
    else:
        avg_sentiment = "neutral"
    
    last_interaction = max(conv.created_at for conv in conversations) if conversations else None
    
    return {
        "total_messages": total_messages,
        "conversations": len(conversations),
        "avg_sentiment": avg_sentiment,
        "last_interaction": last_interaction
    }

# --- Initialize AI Coach ---
@st.cache_resource
def get_ai_coach():
    return GeminiMessageCoach()

ai_coach = get_ai_coach()

# --- API Key Setup UI ---
if not st.session_state.gemini_api_key:
    st.error("🔑 Please configure your Google Gemini API key to use The Third Voice")
    with st.expander("Configure Google Gemini API", expanded=True):
        st.markdown("**Get your free API key:** [Google AI Studio](https://aistudio.google.com/app/apikey)")
        api_key_input = st.text_input("Enter your Gemini API key:", type="password")
        if st.button("Save API Key"):
            if api_key_input:
                try:
                    genai.configure(api_key=api_key_input)
                    test_model = genai.GenerativeModel('gemini-1.5-flash')
                    test_model.generate_content("Test")
                    st.session_state.gemini_api_key = api_key_input
                    st.success("✅ API key validated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Invalid API key: {e}")
    st.stop()

# --- Main App ---
st.markdown("""
<div class="main-header">
    <h1>🎙️ The Third Voice</h1>
    <h3>AI-Powered Emotional Intelligence for Better Communication</h3>
    <p><i>Your co-mediator for life's most challenging conversations</i></p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar: Relationship Management ---
with st.sidebar:
    st.header("🤝 Relationships")
    
    # Add New Relationship
    with st.expander("➕ Add New Relationship"):
        new_name = st.text_input("Name:")
        new_type = st.selectbox("Type:", [e.value for e in RelationshipType])
        new_notes = st.text_area("Notes (optional):")
        
        if st.button("Add Relationship"):
            if new_name:
                new_relationship = Relationship(
                    id=str(uuid.uuid4()),
                    name=new_name,
                    type=RelationshipType(new_type),
                    notes=new_notes
                )
                save_relationship(new_relationship)
                st.success(f"Added {new_name}!")
                st.rerun()
    
    # Display Relationships
    if st.session_state.relationships:
        st.subheader("Your Relationships")
        for rel_id, relationship in st.session_state.relationships.items():
            risk_level = calculate_relationship_risk(rel_id)
            risk_color = {
                EmotionalRisk.LOW: "risk-low",
                EmotionalRisk.MODERATE: "risk-moderate",
                EmotionalRisk.HIGH: "risk-high",
                EmotionalRisk.CRITICAL: "risk-critical"
            }[risk_level]
            
            is_selected = st.session_state.selected_relationship == rel_id
            
            # Create relationship card with clickable selection
            with st.container():
                st.markdown("
      
