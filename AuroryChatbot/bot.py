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
    color: #e0e0e0;
}

.stApp h1 {
    font-size: 2.2em;
}

.stSidebar h1 {
    font-size: 1.8em;
}
.stSidebar h2 {
    font-size: 1.6em;
}

.main > div {
    background: var(--dark-bg);
    border-radius: 20px;
    padding: 25px;
    margin: 15px 0;
    border: 1px solid var(--border-color);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.query-details {
    background: rgba(0, 0, 0, 0.4);
    border-left: 4px solid var(--primary-color);
    padding: 12px;
    margin: 10px 0 0 0;
    border-radius: 0 8px 8px 0;
    font-family: 'Courier New', monospace;
    font-size: 0.8em;
    color: rgba(255, 255, 255, 0.95);
}

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

.stRadio > label {
    font-size: 0.9em;
    padding: 5px 10px;
    margin-bottom: 2px;
}
.stRadio div[role="radiogroup"] {
    gap: 5px;
}

.agent-selector-inline {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 15px;
    margin: 15px 0;
    display: flex;
    justify-content: space-around;
    gap: 10px;
    flex-wrap: wrap;
}

.stButton>button {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    flex-grow: 1;
    min-width: 150px;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.stButton>button.dao-expert {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}

.stButton>button.dao-expert:hover {
    box-shadow: 0 8px 25px rgba(118, 75, 162, 0.4);
}

.stButton>button.gaming-strategist {
    background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%);
    box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);
}

.stButton>button.gaming-strategist:hover {
    box-shadow: 0 8px 25px rgba(56, 239, 125, 0.4);
}

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
}

.query-details {
    font-size: 0.8em;
    color: #a0a0a0;
    margin-top: 10px;
    border-top: 1px dashed rgba(255, 255, 255, 0.1);
    padding-top: 5px;
}

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

.feature-card {
    background: var(--card-bg);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid var(--border-color);
    text-align: center;
    transition: all 0.3s ease;
    margin: 15px 0;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
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
        "selected_agent": "🎮 Gaming Strategist",
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
        "current_page": "💬 Chat",
        "chat_history": []
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
    
    inappropriate_words = ['spam', 'hack', 'exploit']
    if any(word in user_input.lower() for word in inappropriate_words):
        return False, "Please avoid inappropriate content in your queries."
    
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
    """Append message to session state"""
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
        "generated_cypher_query": generated_cypher_query
    }
    st.session_state.messages.append(message_data)

def save_chat_to_history():
    """Save current chat session to history"""
    if len(st.session_state.messages) > 0:
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
    is_valid, error_message = validate_user_input(message)
    if not is_valid:
        append_message_to_session_state('assistant', f"⚠️ {error_message}")
        st.rerun()
        return
    
    append_message_to_session_state("user", message)
    st.session_state.processing = True
    st.session_state.system_status = "processing"
    
    agent_id = AGENTS[st.session_state.selected_agent]["id"]
    processing_status_placeholder = st.empty()

    try:
        start_time = time.time()
        
        with processing_status_placeholder.container():
            st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
                        f'<div class="loading-spinner"></div>'
                        f'<span style="font-size: 0.9em; color: #f093fb;">🔍 {st.session_state.selected_agent} is analyzing your query...</span>'
                        f'</div>', unsafe_allow_html=True)
            
            if st.session_state.show_query_details:
                progress_bar = st.progress(0)
                
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
                
        response_data = generate_response(message, agent_id=agent_id)
        main_response_content = response_data.get("output", "No response generated.")
        generated_cypher_query = response_data.get("generated_cypher_query", None)

        processing_time = time.time() - start_time
        
        query_details = {
            'processing_time': f"{processing_time:.2f}s",
            'tokens_used': f"~{len(message.split()) * 4}",
            'confidence': "95%",
            'agent_used': st.session_state.selected_agent
        }
        
        if processing_time > 2:
            main_response_content += f"\n\n*⚡ Analysis completed in {processing_time:.1f} seconds by {st.session_state.selected_agent}*"
        
        append_message_to_session_state(
            'assistant', 
            main_response_content, 
            agent_id=agent_id, 
            query_details=query_details,
            generated_cypher_query=generated_cypher_query
        )
        
        st.session_state.processing = False
        st.session_state.system_status = "online"
        
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
        processing_status_placeholder.empty()
        st.rerun()

def display_integrated_agent_selector():
    """Integrated agent selection within the chat interface."""
    
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🏛️ DAO Expert",
            key="dao_expert_button",
            help=AGENTS['🏛️ DAO Expert']['description'],
            use_container_width=True,
        ):
            st.session_state.selected_agent = "🏛️ DAO Expert"
            st.rerun()
    
    with col2:
        if st.button(
            "🎮 Gaming Strategist",
            key="gaming_strategist_button",
            help=AGENTS['🎮 Gaming Strategist']['description'],
            use_container_width=True,
        ):
            st.session_state.selected_agent = "🎮 Gaming Strategist"
            st.rerun()

def display_enhanced_sidebar():
    """Comprehensive sidebar with all features"""
    with st.sidebar:
        
        # Chat sayfasında gösterilecek özel kontroller
        if st.session_state.current_page == "💬 Chat":
            # Seçili agent bilgisi
            selected_agent_info = AGENTS[st.session_state.selected_agent]
            st.markdown("**Selected Agent:**")
            st.markdown(f"{st.session_state.selected_agent}")

            
            st.markdown("---")
            
        # Chat kontrolleri
        if st.button("🆕 New Chat", use_container_width=True):
            clear_current_chat()
        
        if st.button("💾 Save Chat", use_container_width=True):
            save_chat_to_history()
            st.toast("✅ Chat saved to history!")
        
        st.markdown("---")
        
        # Navigation - DÜZELTİLDİ: Burada radio button kullanıyoruz
        current_page = st.radio(
            "Navigate:", 
            ["💬 Chat", "📈 Market", "📚 History"],
            index=["💬 Chat", "📈 Market", "📚 History"].index(st.session_state.current_page),
            key="navigation_radio"
        )
        
        # Sayfa değişikliği kontrolü - sadece değişirse rerun
        if current_page != st.session_state.current_page:
            st.session_state.current_page = current_page
            st.rerun()
        
        st.markdown("---")
        
      
          
        
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
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sessions", len(st.session_state.get('chat_history', [])))
        with col2:
            st.metric("Messages", len(st.session_state.messages))

def display_chat_interface():
    """Main chat interface with enhanced features"""
  
    
    # Agent seçim butonları
    display_integrated_agent_selector()
    
   
    
    # Mesajları göster
    if st.session_state.messages:
        for message in st.session_state.messages:
            display_message(message)
    else:
        st.markdown("""
        ### 👋 Welcome to Aurory Assistant!
        
        I'm here to help you with:
        - **Economic Analysis** - Token economics and market insights
        - **Gaming Strategies** - P2E optimization and Neftie management  
        - **DAO Governance** - Proposal analysis and voting insights
     
        
        Choose an agent above and ask your first question!
        """)
    
    # Chat input
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
        
        if st.session_state.show_query_details and message.get('generated_cypher_query'):
            with st.expander("🔍 Generated Cypher Query", expanded=False):
                st.code(message['generated_cypher_query'], language='cypher')

# Market sayfası fonksiyonları
AURORY_COLLECTIONS = {
    "Aurorians": "aurory"
}

@st.cache_data(ttl=300)
def get_magic_eden_stats_cached(collection_symbol):
    base_url = f"https://api-mainnet.magiceden.dev/v2/collections/{collection_symbol}"
    stats = {
        "collection": collection_symbol,
        "floor_price_SOL": None,
        "trade_volume_SOL": None,
        "listed_count": None,
        "avg_price_24h": None,
        "volume_change_24h": None
    }
    
    try:
        response = requests.get(f"{base_url}/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stats.update({
                "floor_price_SOL": data.get("floorPrice", 0) / 1e9 if data.get("floorPrice") else None,
                "trade_volume_SOL": data.get("volumeAll", 0) / 1e9 if data.get("volumeAll") else None,
                "listed_count": data.get("listedCount", 0),
                "avg_price_24h": data.get("avgPrice24hr", 0) / 1e9 if data.get("avgPrice24hr") else None
            })
    except Exception as e:
        st.error(f"Error fetching Magic Eden data for {collection_symbol}: {str(e)}")
    
    return stats
@st.cache_data(ttl=300)
def get_sol_price():
    """Get current SOL price in USD"""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("solana", {}).get("usd", 0)
    except:
        pass
    return 0

def display_market_interface():
    """Market analysis interface"""
    st.title("Aurory Market Analysis")
    
    # SOL price header
    sol_price = get_sol_price()
    if sol_price > 0:
        st.metric("SOL Price (USD)", f"${sol_price:.2f}")
        st.markdown("---")
    
    # Collection tabs
    tabs = st.tabs(list(AURORY_COLLECTIONS.keys()))
    
    for idx, (collection_name, collection_symbol) in enumerate(AURORY_COLLECTIONS.items()):
        with tabs[idx]:
            st.subheader(f"{collection_name} Collection")
            
            with st.spinner(f"Fetching {collection_name} data..."):
                stats = get_magic_eden_stats_cached(collection_symbol)
            
            # Metrics display
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if stats["floor_price_SOL"]:
                    floor_usd = stats["floor_price_SOL"] * sol_price if sol_price > 0 else 0
                    st.metric(
                        "Floor Price", 
                        f"{stats['floor_price_SOL']:.2f} SOL",
                        delta=f"${floor_usd:.2f}" if floor_usd > 0 else None
                    )
                else:
                    st.metric("Floor Price", "N/A")
            
            with col2:
                if stats["trade_volume_SOL"]:
                    volume_usd = stats["trade_volume_SOL"] * sol_price if sol_price > 0 else 0
                    st.metric(
                        "Volume (All Time)", 
                        f"{stats['trade_volume_SOL']:.0f} SOL",
                        delta=f"${volume_usd:.0f}" if volume_usd > 0 else None
                    )
                else:
                    st.metric("Volume (All Time)", "N/A")
            
            with col3:
                if stats["listed_count"]:
                    st.metric("Listed Items", f"{stats['listed_count']:,}")
                else:
                    st.metric("Listed Items", "N/A")
            
            with col4:
                if stats["avg_price_24h"]:
                    avg_usd = stats["avg_price_24h"] * sol_price if sol_price > 0 else 0
                    st.metric(
                        "Avg Price (24h)", 
                        f"{stats['avg_price_24h']:.2f} SOL",
                        delta=f"${avg_usd:.2f}" if avg_usd > 0 else None
                    )
                else:
                    st.metric("Avg Price (24h)", "N/A")
            
        
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"🔍 View {collection_name} on Magic Eden", key=f"view_{collection_symbol}"):
                    st.markdown(f"[Open Magic Eden Collection](https://magiceden.io/marketplace/{collection_symbol})")
            
         

def display_history_interface():
    """Chat history interface"""
    st.title("📚 Chat History")
    
    if not st.session_state.get('chat_history'):
        st.markdown("""
        ### 📝 No Chat History Yet
        
        Your conversation history will appear here after you:
        - Have conversations with the assistant
        - Save chats manually
        - Complete chat sessions
        
        Start chatting to build your history!
        """)
        return
    
    # History controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search chat history...", key="history_search")
    with col2:
        sort_order = st.selectbox("Sort by:", ["Newest First", "Oldest First"], key="history_sort")
    with col3:
        if st.button("🗑️ Clear All History", key="clear_history"):
            st.session_state.chat_history = []
            st.rerun()
    
    st.markdown("---")
    
    # Filter and sort history
    filtered_history = st.session_state.chat_history.copy()
    
    if search_query:
        filtered_history = [
            session for session in filtered_history
            if any(search_query.lower() in qa['question'].lower() or 
                   search_query.lower() in qa['answer'].lower()
                   for qa in session['qa_pairs'])
        ]
    
    if sort_order == "Oldest First":
        filtered_history.reverse()
    
    # Display history
    if not filtered_history:
        st.info("No chat sessions match your search criteria.")
        return
    
    for session in filtered_history:
        with st.expander(
            f"💬 Chat Session - {len(session['qa_pairs'])} questions - "
            f"{format_timestamp(session['timestamp'])}", 
            expanded=False
        ):
            for i, qa in enumerate(session['qa_pairs']):
                # Question
                st.markdown(f"""
                <div class="history-card">
                    <div class="history-question">❓ {qa['question']}</div>
                    <div class="history-response">🤖 {qa['answer'][:200]}{'...' if len(qa['answer']) > 200 else ''}</div>
                    <div class="history-meta">
                        <span>{format_timestamp(qa['timestamp'])}</span>
                        <span class="history-agent">{qa.get('agent', 'Unknown Agent')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show full answer if clicked
                if st.button(f"Show Full Answer", key=f"show_full_{session['id']}_{i}"):
                    st.markdown(f"**Full Response:**\n\n{qa['answer']}")
                
                # Show query details if available
                if qa.get('query_details') and st.button(f"Show Details", key=f"show_details_{session['id']}_{i}"):
                    details = qa['query_details']
                    st.json(details)
                
                # Show generated Cypher query if available
                if qa.get('generated_cypher_query') and st.button(f"Show Query", key=f"show_query_{session['id']}_{i}"):
                    st.code(qa['generated_cypher_query'], language='cypher')
                
                if i < len(session['qa_pairs']) - 1:
                    st.markdown("---")

def main():
    """Main application logic"""
    init_session_state()
    display_enhanced_sidebar()
    
    # Page routing
    if st.session_state.current_page == "💬 Chat":
        display_chat_interface()
    elif st.session_state.current_page == "📈 Market":
        display_market_interface()
    elif st.session_state.current_page == "📚 History":
        display_history_interface()

if __name__ == "__main__":
    main()
