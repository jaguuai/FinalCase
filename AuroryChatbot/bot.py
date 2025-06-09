import streamlit as st
from agent import generate_response # Bu modülün var olduğunu varsayıyorum
import time
import uuid
from datetime import datetime, timedelta
import requests
from pytz import timezone

# --- Page Configuration ---
st.set_page_config(
    page_title="Aurory Assistant",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --accent-color: #11998e;
    --success-color: #38ef7d;
    --warning-color: #f093fb;
    --error-color: #ff6b6b;
    --dark-bg: #0f0f23;
    --card-bg: rgba(255, 255, 255, 0.05);
    --border-color: rgba(255, 255, 255, 0.1);
}

.stApp {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, var(--dark-bg) 0%, #1a1a2e 50%, #16213e 100%);
    color: #e0e0e0; /* Varsayılan metin rengi */
}

/* Ana başlık (Aurory Economic Strategy Assistant) için boyut küçültme */
.stApp h1 {
    font-size: 2.2em; /* Varsayılanı küçültüldü */
}

/* Sidebar başlığı (Agent Seçimi) için boyut küçültme */
.stSidebar h1 { /* Eğer h1 olarak render ediliyorsa */
    font-size: 1.8em; /* Küçültüldü */
}
.stSidebar h2 { /* Eğer h2 olarak render ediliyorsa (bazı Streamlit versiyonlarında bu olabilir) */
    font-size: 1.6em; /* Küçültüldü */
}

/* Ana içerik alanı - Streamlit'in kendi layout'una güveniyoruz, çok az müdahale */
.main > div {
    background: var(--dark-bg); /* Sadece arka plan ve genel stil */
    border-radius: 20px;
    padding: 25px;
    margin: 15px 0;
    border: 1px solid var(--border-color);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Query Details - hala görünebilir olmalı */
.query-details {
    background: rgba(0, 0, 0, 0.4); /* Daha koyu arka plan */
    border-left: 4px solid var(--primary-color);
    padding: 12px;
    margin: 10px 0 0 0;
    border-radius: 0 8px 8px 0;
    font-family: 'Courier New', monospace;
    font-size: 0.8em;
    color: rgba(255, 255, 255, 0.95); /* Çok açık metin rengi */
}

/* History card styles */
.history-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    transition: all 0.3s ease;
}

.history-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    border-color: var(--primary-color);
}

.history-question {
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 8px;
    font-size: 1.1em;
}

.history-response {
    color: #b0b0b0;
    font-size: 0.9em;
    margin-bottom: 8px;
    max-height: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8em;
    color: #888;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--border-color);
}

.history-agent {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.7em;
    font-weight: 500;
}

/* Diğer bileşenlerin stilleri aynı kalır */
.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.status-online { background-color: var(--success-color); }
.status-processing { background-color: var(--warning-color); }
.status-error { background-color: var(--error-color); }

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

# .feature-grid {
#     display: grid;
#     grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
#     gap: 15px;
#     margin: 20px 0;
# }

# .feature-card {
#     background: var(--card-bg);
#     padding: 20px;
#     border-radius: 15px;
#     border: 1px solid var(--border-color);
#     text-align: center;
#     transition: all 0.3s ease;
# }

# .feature-card:hover {
#     transform: translateY(-5px);
#     box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
# }

.metric-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    padding: 15px;
    border-radius: 12px;
    margin: 8px 0;
    text-align: center;
    border: 1px solid var(--border-color);
    transition: transform 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
}

/* Agent seçim radyo butonları için boyut küçültme */
.stRadio > label {
    font-size: 0.9em; /* Yazı boyutunu küçültür */
    padding: 5px 10px; /* İç boşluğu azaltır */
    margin-bottom: 2px; /* Butonlar arası boşluğu azaltır */
}
.stRadio div[role="radiogroup"] {
    gap: 5px; /* Radyo butonları arasındaki boşluğu ayarlar */
}

.agent-selector-inline { /* Yeni stil adı */
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 15px;
    margin: 15px 0;
    display: flex;
    justify-content: space-around; /* Butonları eşit dağıt */
    gap: 10px; /* Butonlar arası boşluk */
    flex-wrap: wrap; /* Küçük ekranlarda alt alta geçiş */
}

/* Streamlit Button Overrides for Agent Selection */
.stButton>button.agent-button {
    background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%); /* Green for gaming */
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    flex-grow: 1; /* Make buttons grow to fill space */
    min-width: 150px; /* Minimum width for buttons */
}

.stButton>button.agent-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
}

.stButton>button.agent-button.dao-expert {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); /* Purple/Blue for DAO */
    box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}

.stButton>button.agent-button.dao-expert:hover {
    box-shadow: 0 8px 25px rgba(118, 75, 162, 0.4);
}


/* Streamlit Input fields */
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    color: white;
    padding: 10px 15px;
}

h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
    font-weight: 600;
}

.sidebar-section {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 15px;
    margin: 15px 0;
    border: 1px solid var(--border-color);

.query-details {
    font-size: 0.8em;
    color: #a0a0a0;
    margin-top: 10px;
    border-top: 1px dashed rgba(255, 255, 255, 0.1);
    padding-top: 5px;
}
}
</style>
""", unsafe_allow_html=True)


# --- Agent Configuration ---
AGENTS = {
    "🏛️ DAO Expert": {
        "id": "dao",
        "description": "Governance and community decision specialist",
        "capabilities": ["Proposal analysis", "Voting patterns", "Community insights"],
        "color": "#764ba2",
        "css_class": "dao-expert"
    },
    "🎮 Gaming Strategist": {
        "id": "gaming",
        "description": "P2E optimization and gaming economics",
        "capabilities": ["Neftie strategies", "Guild management", "Earning optimization"],
        "color": "#38ef7d",
        "css_class": "gaming-strategist"
    }
}

# --- Utility Functions ---
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "messages": [],
        "selected_agent": "🎮 Gaming Strategist", # Default agent
        "show_query_details": False,
        "show_timestamps": True,
        "theme": "dark",
        "auto_scroll": True,
        "system_status": "online",
        "processing": False,
        "session_id": str(uuid.uuid4()),
        "user_preferences": {
            "notifications": True,
            "sound": False,
            "compact_mode": False
        },
        "current_page": "💬 Chat", # Initialize the current page
        "chat_history": [] # Store all chat sessions
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def validate_user_input(user_input: str) -> tuple[bool, str]:
    """Enhanced input validation with comprehensive checks"""
    if not user_input or not user_input.strip():
        return False, "Please enter a question about Aurory's ecosystem."
    
    if len(user_input) > 2000:
        return False, "Please keep questions under 2000 characters for optimal processing."
    
    # Check for inappropriate content
    inappropriate_words = ['spam', 'hack', 'exploit']
    if any(word in user_input.lower() for word in inappropriate_words):
        return False, "Please avoid inappropriate content in your queries."
    
    # Aurory-related keywords (expanded)
    aurory_keywords = [
        'aurory', 'aury', 'xaury', 'nerite', 'ember', 'wisdom', 'neftie', 
        'aurorian', 'dao', 'p2e', 'token', 'nft', 'game', 'economy', 'guild',
        'staking', 'yield', 'farming', 'defi', 'governance', 'proposal', 'vote',
        'trading', 'market', 'price', 'chart', 'analysis', 'strategy'
    ]
    
    if not any(keyword in user_input.lower() for keyword in aurory_keywords) and len(user_input) > 50:
        return False, "I specialize in Aurory ecosystem analysis. Please ask about Aurory-related topics."
    
    return True, ""


def create_message_id():
    """Generate unique message ID"""
    return f"msg_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.seconds < 60:
        return "Just now"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}m ago"
    elif diff.days == 0:
        return timestamp.strftime("%H:%M")
    elif diff.days == 1:
        return f"Yesterday {timestamp.strftime('%H:%M')}"
    else:
        return timestamp.strftime("%m/%d %H:%M")

def append_message_to_session_state(role, content, agent_id=None, query_details=None, generated_cypher_query=None):
    """Append message to session state, not for direct rendering"""
    message_id = create_message_id()
    timestamp = datetime.now()
    message_data = {
        "id": message_id,
        "role": role,
        "content": content,
        "timestamp": timestamp.isoformat(),
        "agent_id": agent_id,
        "query_details": query_details,
        "is_favorite": False,
        "generated_cypher_query": generated_cypher_query # Add this line
    }
    st.session_state.messages.append(message_data)

def save_chat_to_history():
    """Save current chat session to history"""
    if len(st.session_state.messages) > 0:
        # Find user questions and assistant responses
        qa_pairs = []
        current_question = None
        
        for message in st.session_state.messages:
            if message["role"] == "user":
                current_question = message
            elif message["role"] == "assistant" and current_question:
                qa_pairs.append({
                    "question": current_question["content"],
                    "answer": message["content"],
                    "timestamp": current_question["timestamp"],
                    "agent": message.get("agent_id", "unknown"),
                    "query_details": message.get("query_details"),
                    "generated_cypher_query": message.get("generated_cypher_query")
                })
                current_question = None
        
        if qa_pairs:
            chat_session = {
                "id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "qa_pairs": qa_pairs,
                "total_questions": len(qa_pairs)
            }
            
            # Add to history (keep last 50 sessions)
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            st.session_state.chat_history.insert(0, chat_session)
            if len(st.session_state.chat_history) > 50:
                st.session_state.chat_history.pop()

def clear_current_chat():
    """Clear current chat and start new session"""
    save_chat_to_history()
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

def handle_submit(message):
    """Enhanced message processing with detailed analytics"""
    # Validate input
    is_valid, error_message = validate_user_input(message)
    if not is_valid:
        # Append error message to session state
        append_message_to_session_state('assistant', f"⚠️ {error_message}")
        st.rerun() # Re-run to show the new message
        return
    
    # Add user message to chat history
    append_message_to_session_state("user", message)

    # Set processing status
    st.session_state.processing = True
    st.session_state.system_status = "processing"
    
    # Get selected agent
    agent_id = AGENTS[st.session_state.selected_agent]["id"]
    
    # Use a single placeholder for processing messages
    processing_status_placeholder = st.empty()

    try:
        start_time = time.time()
        
        # Display initial loading message
        with processing_status_placeholder.container():
            st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                        f'<div class="loading-spinner"></div>'
                        f'<span style="font-size: 0.9em; color: #f093fb;">🔍 {st.session_state.selected_agent} is analyzing your query...</span>'
                        f'</div>', unsafe_allow_html=True)
            
            # Show detailed processing steps if query details are enabled
            if st.session_state.show_query_details:
                progress_bar = st.progress(0)
                
                # Update status messages within the placeholder
                processing_status_placeholder.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                                                f'<div class="loading-spinner"></div>'
                                                f'<span style="font-size: 0.9em; color: #f093fb;">🔍 Parsing query...</span>'
                                                f'</div>', unsafe_allow_html=True)
                progress_bar.progress(20)
                time.sleep(0.3)
                
                processing_status_placeholder.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                                                f'<div class="loading-spinner"></div>'
                                                f'<span style="font-size: 0.9em; color: #f093fb;">🧠 Selecting optimal agent...</span>'
                                                f'</div>', unsafe_allow_html=True)
                progress_bar.progress(40)
                time.sleep(0.3)
                
                processing_status_placeholder.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                                                f'<div class="loading-spinner"></div>'
                                                f'<span style="font-size: 0.9em; color: #f093fb;">📊 Fetching relevant data...</span>'
                                                f'</div>', unsafe_allow_html=True)
                progress_bar.progress(60)
                time.sleep(0.3)
                
                processing_status_placeholder.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                                                f'<div class="loading-spinner"></div>'
                                                f'<span style="font-size: 0.9em; color: #f093fb;">🤖 Generating intelligent response...</span>'
                                                f'</div>', unsafe_allow_html=True)
                progress_bar.progress(80)
                time.sleep(0.3)
                
                processing_status_placeholder.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                                                f'<div class="loading-spinner"></div>'
                                                f'<span style="font-size: 0.9em; color: #f093fb;">✨ Finalizing analysis...</span>'
                                                f'</div>', unsafe_allow_html=True)
                progress_bar.progress(100)
                time.sleep(0.2)
                
        # Generate response
        response_data = generate_response(message, agent_id=agent_id) # Call generates_response and get the dictionary
        
        # Extract the main output and the Cypher query
        main_response_content = response_data.get("output", "No response generated.")
        generated_cypher_query = response_data.get("generated_cypher_query", None)

        processing_time = time.time() - start_time
        
        # Create query details
        query_details = {
            'processing_time': f"{processing_time:.2f}s",
            'tokens_used': f"~{len(message.split()) * 4}", # Placeholder for token count
            'confidence': "95%", # Placeholder for confidence
            'agent_used': st.session_state.selected_agent
        }
        
        # Add processing info for longer queries
        if processing_time > 2:
            main_response_content += f"\n\n*⚡ Analysis completed in {processing_time:.1f} seconds by {st.session_state.selected_agent}*"
        
        # Append response to session state, passing the Cypher query as well
        append_message_to_session_state(
            'assistant', 
            main_response_content, 
            agent_id=agent_id, 
            query_details=query_details,
            generated_cypher_query=generated_cypher_query # Pass the Cypher query here
        )
        
        # Reset status
        st.session_state.processing = False
        st.session_state.system_status = "online"
        
        # Show success notification
        if st.session_state.user_preferences["notifications"]:
            st.toast("✅ Response generated successfully!")
        
    except Exception as e:
        st.session_state.processing = False
        st.session_state.system_status = "error"
        
        error_response = f"""
        🚨 **Analysis Error**
        
        I encountered an issue while processing your request. This could be due to:
        • High server load or temporary service interruption
        • Complex query requiring specialized processing
        • Network connectivity issues
        
        **Troubleshooting Steps:**
        1. **Try again** - The issue might be temporary
        2. **Simplify your query** - Break complex questions into smaller parts
        3. **Switch agent** - Try a different specialized agent
        4. **Check system status** - Look for any ongoing maintenance
        
        **Need immediate help?** Contact our support team with error code: `{str(e)[:50]}`
        
        *Error occurred at: {datetime.now().strftime('%H:%M:%S')}*
        """
        append_message_to_session_state('assistant', error_response)
        st.error(f"⚠️ Processing error: {str(e)}")
    finally:
        # Clear the entire placeholder container
        processing_status_placeholder.empty()
        # Ensure a rerun to clear the input field and update the chat history
        st.rerun()


def display_integrated_agent_selector():
    """Integrated agent selection within the chat interface."""

    
    cols = st.columns(len(AGENTS))
    agent_names = list(AGENTS.keys())

    # Dynamically apply CSS classes to buttons
    button_css = """
    <style>
    .stButton>button {
        /* Default button styles */
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        flex-grow: 1; /* Make buttons grow to fill space */
        min-width: 150px; /* Minimum width for buttons */
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    """
    
    # Add specific styles for each agent button
    for agent_name, agent_info in AGENTS.items():
        if 'css_class' in agent_info:
            if agent_info['css_class'] == "dao-expert":
                button_css += f"""
                .stButton>button[key*="agent_{agent_info['id']}_button"] {{
                    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                    box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
                }}
                .stButton>button[key*="agent_{agent_info['id']}_button"]:hover {{
                    box-shadow: 0 8px 25px rgba(118, 75, 162, 0.4);
                }}
                """
            elif agent_info['css_class'] == "gaming-strategist":
                button_css += f"""
                .stButton>button[key*="agent_{agent_info['id']}_button"] {{
                    background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%);
                    box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);
                }}
                .stButton>button[key*="agent_{agent_info['id']}_button"]:hover {{
                    box-shadow: 0 8px 25px rgba(56, 239, 125, 0.4);
                }}
                """
    
    st.markdown(button_css, unsafe_allow_html=True)


    with st.container(): # Use a container to group the buttons and selected info
        col1, col2 = st.columns(2) # Two columns for the two agent buttons

        with col1:
            if st.button(
                "🏛️ DAO Expert",
                key=f"agent_{AGENTS['🏛️ DAO Expert']['id']}_button",
                help=AGENTS['🏛️ DAO Expert']['description'],
                use_container_width=True,
            
            ):
                st.session_state.selected_agent = "🏛️ DAO Expert"
                st.rerun() # Rerun to update the displayed active agent and perhaps chat history
        
        with col2:
            if st.button(
                "🎮 Gaming Strategist",
                key=f"agent_{AGENTS['🎮 Gaming Strategist']['id']}_button",
                help=AGENTS['🎮 Gaming Strategist']['description'],
                use_container_width=True,
                # className=AGENTS['🎮 Gaming Strategist']['css_class']
            ):
                st.session_state.selected_agent = "🎮 Gaming Strategist"
                st.rerun() # Rerun to update the displayed active agent and perhaps chat history

   

def display_enhanced_sidebar():
    """Comprehensive sidebar with all features"""
    with st.sidebar:
        # Agent capabilities
        if st.session_state.current_page == "💬 Chat":
         
            selected_agent_info = AGENTS[st.session_state.selected_agent]
            st.markdown("Selected Agent: ")
            st.markdown(f"**{st.session_state.selected_agent}**")
                    
            st.markdown("---")
            
        if st.session_state.current_page == "💬 Chat":
        
            
            if st.button("🆕 New Chat", use_container_width=True):
                clear_current_chat()
            
            if st.button("💾 Save Chat", use_container_width=True):
                save_chat_to_history()
                st.toast("✅ Chat saved to history!")
            
            st.markdown("---")
 
        # Agent capabilities
        if st.session_state.current_page == "💬 Chat":
         
            selected_agent_info = AGENTS[st.session_state.selected_agent]
            
            st.markdown(f"**{st.session_state.selected_agent}**")
 
      
        # Navigation - Added History

        st.session_state.current_page = st.radio(
            "Choose Page:", 
            ["💬 Chat", "📈 Market", "📚 History"], # Added History
            key="navigation"
        )
        
        st.markdown("---")
        
        # Chat Controls (only show on chat page)
       
        
        # Quick Settings
      
        # Advanced Options
        st.markdown("**Advanced Options:**")
        st.session_state.show_query_details = st.checkbox(
            "Show Query Details", 
            value=st.session_state.show_query_details,
            help="Display processing information and metadata"
        )
        
        st.session_state.show_timestamps = st.checkbox(
            "Show Timestamps", 
            value=st.session_state.show_timestamps,
            help="Display message timestamps"
        )
        
        st.session_state.auto_scroll = st.checkbox(
            "Auto Scroll", 
            value=st.session_state.auto_scroll,
            help="Automatically scroll to latest messages"
        )
        
        st.markdown("---")
        
        # System Info
        st.markdown("### 📊 System Status")
        
        # Create metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sessions", len(st.session_state.get('chat_history', [])))
        with col2:
            st.metric("Messages", len(st.session_state.messages))
        
        
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; font-size: 0.8em; opacity: 0.6;'>
    
        </div>
        """, unsafe_allow_html=True)

def display_chat_interface():
    """Main chat interface with enhanced features"""
    
    # Sadece agent seçim butonlarını göster
    display_integrated_agent_selector()
    
    # Mesajları göster
    if st.session_state.messages:
        for message in st.session_state.messages:
            display_message(message)
    
    # Sohbet inputu (her zaman sayfanın altında)
    user_input = st.chat_input(
        "Ask about Aurory ecosystem, token economics, governance, or gaming strategies...",
        key="chat_input",
        disabled=st.session_state.processing
    )

    if user_input:
        handle_submit(user_input)

def display_message(message):
    """Enhanced message display with better formatting"""
    timestamp = format_timestamp(message['timestamp'])
    
    if message['role'] == 'user':
        # User message
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
            <div style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
                        color: white; padding: 12px 16px; border-radius: 15px 15px 5px 15px; 
                        max-width: 70%; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <strong>You:</strong> {message['content']}
                {f'<div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">{timestamp}</div>' if st.session_state.show_timestamps else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Assistant message
        agent_emoji = "🏛️" if message.get('agent_id') == 'dao' else "🎮"
        agent_name = "DAO Expert" if message.get('agent_id') == 'dao' else "Gaming Strategist"
        
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
            <div style="background: var(--card-bg); border: 1px solid var(--border-color); 
                        color: #e0e0e0; padding: 12px 16px; border-radius: 15px 15px 15px 5px; 
                        max-width: 70%; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <strong>{agent_emoji} {agent_name}:</strong>
                <div style="margin-top: 8px;">{message['content']}</div>
                {f'<div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">{timestamp}</div>' if st.session_state.show_timestamps else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Query details if enabled
        if st.session_state.show_query_details and message.get('query_details'):
            details = message['query_details']
            st.markdown(f"""
            <div class="query-details">
                <strong>Query Analytics:</strong><br>
                • Processing Time: {details.get('processing_time', 'N/A')}<br>
                • Tokens Used: {details.get('tokens_used', 'N/A')}<br>
                • Confidence: {details.get('confidence', 'N/A')}<br>
                • Agent: {details.get('agent_used', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
        
        # Show Cypher query if available
        if st.session_state.show_query_details and message.get('generated_cypher_query'):
            with st.expander("🔍 Generated Cypher Query", expanded=False):
                st.code(message['generated_cypher_query'], language='cypher')




AURORY_COLLECTIONS = {
    "Aurorians": "aurory",
    "Accessories": "aurory_accessories",
    "Missions": "aurory_missions"
}

@st.cache_data(ttl=300) # Cache data for 5 minutes to avoid hitting API limits
def get_magic_eden_stats_cached(collection_symbol):
    base_url = f"https://api-mainnet.magiceden.dev/v2/collections/{collection_symbol}"
    stats = {
        "collection": collection_symbol,
        "floor_price_SOL": None,
        "trade_volume_SOL": None,
        "mint_rate_events_per_sec": None,
        "last_mint_time": None
    }

    try:
        # 1. Floor price ve volume bilgisi
        stats_url = f"{base_url}/stats"
        st.write(f"Fetching stats from: {stats_url}") # Debugging
        stats_resp = requests.get(stats_url, timeout=10)
        stats_resp.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        stats_data = stats_resp.json()
        
        # Magic Eden floorPrice ve volumeAll değerlerini lamports'tan SOL'e çevir
        stats["floor_price_SOL"] = (stats_data.get("floorPrice") / 1e9) if stats_data.get("floorPrice") else None
        stats["trade_volume_SOL"] = (stats_data.get("volumeAll") / 1e9) if stats_data.get("volumeAll") else None

        # 2. Mint aktiviteleri (daha güvenilir yöntem, son 100 listing'e bak)
        listings_url = f"{base_url}/listings?offset=0&limit=100"
        st.write(f"Fetching listings from: {listings_url}") # Debugging
        listings_resp = requests.get(listings_url, timeout=15)
        listings_resp.raise_for_status()
        listings = listings_resp.json()
        
        mint_times = []
        for item in listings:
            if item.get('createdAt'):
                try:
                    # createdAt formatını düzeltin:YYYY-MM-DDTHH:MM:SS.sssZ
                    mint_time = datetime.strptime(item['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                    mint_times.append(mint_time)
                except ValueError:
                    # Alternatif formatları dene, örn:YYYY-MM-DDTHH:MM:SSZ
                    try:
                        mint_time = datetime.strptime(item['createdAt'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                        mint_times.append(mint_time)
                    except Exception as date_e: # Catch general exception for date parsing
                        st.warning(f"Could not parse date '{item['createdAt']}': {date_e}") # Debugging date format
                        continue # Format uygun değilse atla
        
        # Mint oranını hesapla
        if len(mint_times) >= 2:
            mint_times.sort()
            # Son 5 mint arasındaki ortalama farkı al (daha güncel bir ortalama için)
            if len(mint_times) > 5:
                recent_mint_times = mint_times[-5:]
            else:
                recent_mint_times = mint_times
            
            time_diffs = [recent_mint_times[i] - recent_mint_times[i-1] for i in range(1, len(recent_mint_times))]
            
            avg_interval = sum(time_diffs) / len(time_diffs) if time_diffs else 0
            stats["mint_rate_events_per_sec"] = 1 / avg_interval if avg_interval > 0 else 0
            stats["last_mint_time"] = datetime.fromtimestamp(mint_times[-1]).isoformat()
        elif mint_times:
            stats["last_mint_time"] = datetime.fromtimestamp(mint_times[0]).isoformat()
            
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ API connection error for {collection_symbol}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"HTTP Status: {e.response.status_code}")
            st.error(f"Response Content: {e.response.text}")
        print(f"⛔ API error ({collection_symbol}): {str(e)[:80]}")
    except Exception as e:
        st.error(f"⚠️ An unexpected error occurred for {collection_symbol}: {str(e)}")
        print(f"⛔ General error ({collection_symbol}): {str(e)[:80]}")

    return stats

# Example usage (assuming this is within a Streamlit app):
if __name__ == '__main__':
    st.title("Magic Eden Collection Stats")

    selected_collection = st.selectbox(
        "Select an Aurory Collection:",
        list(AURORY_COLLECTIONS.keys())
    )

    if selected_collection:
        symbol = AURORY_COLLECTIONS[selected_collection]
        stats = get_magic_eden_stats_cached(symbol)
        
        if stats:
            st.subheader(f"Stats for {selected_collection} ({stats['collection']})")
            st.write(f"**Floor Price:** {stats['floor_price_SOL']:.2f} SOL" if stats['floor_price_SOL'] is not None else "N/A")
            st.write(f"**Total Trade Volume:** {stats['trade_volume_SOL']:.2f} SOL" if stats['trade_volume_SOL'] is not None else "N/A")
            st.write(f"**Mint Rate (events/sec):** {stats['mint_rate_events_per_sec']:.4f}" if stats['mint_rate_events_per_sec'] is not None else "N/A")
            st.write(f"**Last Mint Time:** {stats['last_mint_time']}" if stats['last_mint_time'] is not None else "N/A")
        else:
            st.warning("Could not retrieve stats for the selected collection.")


def format_stat_value(value, format_str=".4f"):
    if value is None:
        return "N/A"
    try:
        if isinstance(value, float):
            return f"{value:{format_str}}"
        return str(value)
    except:
        return str(value)

def display_market_page():
    """Market analysis page"""
    st.title("📈 Market Analysis")
    st.markdown("*Real-time Aurory ecosystem market insights*")
    
    # Aurorians koleksiyonu için verileri çek
    aurorians_symbol = AURORY_COLLECTIONS["Aurorians"]
    aurorians_stats = get_magic_eden_stats_cached(aurorians_symbol)

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Aurorians Floor Price (Taban Fiyat)
        floor_price = format_stat_value(aurorians_stats["floor_price_SOL"], ".2f") if aurorians_stats["floor_price_SOL"] else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Aurorians Floor Price</h3>
            <h2 style="color: var(--success-color);">{floor_price} SOL</h2>
            <p style="color: var(--success-color);"> </p> </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Market Cap (Bu bilgi Magic Eden API'sinden gelmiyor, statik kalacak)
        st.markdown("""
        <div class="metric-card">
            <h3>Market Cap</h3>
            <h2>$12.5M</h2>
            <p style="color: var(--warning-color);">-2.1% 24h</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Aurorians Trade Volume (İşlem Hacmi)
        trade_volume = format_stat_value(aurorians_stats["trade_volume_SOL"], ".0f") if aurorians_stats["trade_volume_SOL"] else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Aurorians Volume</h3>
            <h2>{trade_volume} SOL</h2>
            <p style="color: var(--success-color);"> </p> </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Active Players (Bu bilgi Magic Eden API'sinden gelmiyor, statik kalacak)
        st.markdown("""
        <div class="metric-card">
            <h3>Active Players</h3>
            <h2>2,847</h2>
            <p style="color: var(--success-color);">+8.7% 24h</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Market analysis tools
    st.markdown("### 🔍 Analysis Tools")
    
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Price Chart</h4>
            <p>Interactive price and volume charts</p>
            <button style="background: var(--primary-color); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer;">View Chart</button>
        </div>
        """, unsafe_allow_html=True)
    
    with analysis_col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🎯 Technical Analysis</h4>
            <p>AI-powered market trend analysis</p>
            <button style="background: var(--secondary-color); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer;">Analyze</button>
        </div>
        """, unsafe_allow_html=True)


from history import (
    save_current_chat_to_neo4j,
    load_all_chat_sessions_from_neo4j,
    load_specific_chat_session_from_neo4j,
)



def display_history_page():
    """Displays chat history loaded from Neo4j."""
    st.title("📚 Chat History")

    # 1. Neo4j'den tüm mevcut sohbet oturumlarının listesini yükle
    # Bu sadece oturum ID'lerini, zaman damgalarını ve mesaj sayılarını getirir,
    # her oturumun tüm mesajlarını hemen yüklemez.
    all_neo4j_sessions = load_all_chat_sessions_from_neo4j()

    if not all_neo4j_sessions:
        st.info("No chat sessions found in Neo4j. Start a chat and click 'New Chat' to save it!")
        return

    # 2. Streamlit selectbox için seçenekleri ve format_func'ı hazırla
    options_for_selectbox = [s["id"] for s in all_neo4j_sessions]
    # Selectbox'ta gösterilecek metni belirleyen fonksiyon
    format_func_for_selectbox = lambda x: f"Session {x[:8]}... ({next((s['timestamp'] for s in all_neo4j_sessions if s['id'] == x), 'N/A')})"

    selected_session_id = st.selectbox(
        "Select a chat session:",
        options=options_for_selectbox,
        format_func=format_func_for_selectbox,
        key="history_session_selector" # Unique key for the selectbox
    )

    if selected_session_id:
        # 3. Seçilen oturumun tüm mesajlarını Neo4j'den yükle
        # Bu fonksiyon doğrudan mesajların listesini döndürür (user ve assistant mesajları ayrı ayrı).
        session_messages = load_specific_chat_session_from_neo4j(selected_session_id)
        
        # Seçilen oturumun genel bilgilerini (timestamp, total_messages) almak için
        # all_neo4j_sessions listesinden ilgili oturumu bul
        session_info = next((s for s in all_neo4j_sessions if s["id"] == selected_session_id), None)

        if session_info and session_messages:
            st.subheader(f"Session Details: {selected_session_id[:8]}...")
            st.write(f"**Timestamp:** {format_timestamp(session_info['timestamp'])}")
            # Neo4j'den gelen total_messages özelliğini kullan
            st.write(f"**Total Messages:** {session_info.get('total_messages', 'N/A')}")
            
            # 4. Yüklenen mesajları döngüye al ve göster
            # Burada 'qa_pairs' kavramı yerine doğrudan 'messages' listesini kullanıyoruz,
            # çünkü load_specific_chat_session_from_neo4j zaten her mesajı ayrı bir dict olarak getiriyor.
            for j, msg_data in enumerate(session_messages):
                # Her mesaj bir kullanıcı veya asistan mesajı olabilir
                # display_message fonksiyonu role'e göre otomatik olarak formatlar
                display_message(msg_data)
                
                # Mesajlar arasına ayırıcı çizgi koy
                if j < len(session_messages) - 1:
                    st.markdown("---")
        else:
            st.warning("Could not load details for the selected session.")

# --- Main Application ---
def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Display sidebar
    display_enhanced_sidebar()
    
    # Main content based on selected page
    if st.session_state.current_page == "💬 Chat":
        display_chat_interface()
    elif st.session_state.current_page == "📈 Market":
        display_market_page()
    elif st.session_state.current_page == "📚 History":
        display_history_page()
    
    # Add loading spinner CSS
    st.markdown("""
    <style>
    .loading-spinner {
        border: 2px solid #f3f3f3;
        border-top: 2px solid var(--primary-color);
        border-radius: 50%;
        width: 20px;
        height: 20px;
        animation: spin 1s linear infinite;
        display: inline-block;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
                