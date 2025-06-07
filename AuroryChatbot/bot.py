import streamlit as st
from utils import write_message
from agent import generate_response
import time
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Aurory Economic Strategy Assistant",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced CSS Styling ---
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        border-radius: 12px;
        padding: 10px 24px;
        margin-top: 10px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #262730;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    .main > div {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 5px 18px;
        margin: 8px 0;
        margin-left: 15%;
        max-width: 80%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 5px;
        margin: 8px 0;
        margin-right: 15%;
        max-width: 80%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    .message-header {
        font-size: 0.8em;
        opacity: 0.8;
        margin-bottom: 5px;
    }
    .sidebar-stats {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.2);
        padding: 8px;
        border-radius: 8px;
        margin: 5px 0;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def validate_user_input(user_input: str) -> tuple[bool, str]:
    """Validate user input before processing"""
    if not user_input or not user_input.strip():
        return False, "Please enter a question about Aurory economy."
    
    if len(user_input) > 500:
        return False, "Please keep questions under 500 characters for better analysis."
    
    # Check for Aurory-related content (more flexible)
    aurory_keywords = ['aurory', 'aury', 'xaury', 'nerite', 'ember', 'wisdom', 'neftie', 'aurorian', 'dao', 'p2e', 'token', 'nft', 'game', 'economy']
    if not any(keyword in user_input.lower() for keyword in aurory_keywords) and len(user_input) > 50:
        return False, "I specialize in Aurory ecosystem analysis. Please ask about Aurory tokens, NFTs, gameplay, or DAO governance."
    
    return True, ""

def get_message_type_icon(content: str) -> str:
    """Determine message type and return appropriate icon"""
    content_lower = content.lower()
    
    if any(indicator in content_lower for indicator in ['price', '$', 'token', 'trading', 'market']):
        return "💰"
    elif any(indicator in content_lower for indicator in ['dao', 'proposal', 'vote', 'governance']):
        return "🏛️"
    elif any(indicator in content_lower for indicator in ['nft', 'neftie', 'aurorian', 'collectible']):
        return "🎨"
    elif any(indicator in content_lower for indicator in ['game', 'play', 'strategy', 'guild']):
        return "🎮"
    else:
        return "💬"

def display_conversation_stats():
    """Display conversation analytics in sidebar"""
    if not hasattr(st.session_state, 'messages') or len(st.session_state.messages) <= 1:
        return
        
    with st.sidebar:
        st.markdown("### 📊 Session Analytics")
        
        # Basic stats
        total_messages = len(st.session_state.messages)
        user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <strong>{total_messages}</strong><br>
                <small>Total Messages</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <strong>{len(user_messages)}</strong><br>
                <small>Your Questions</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Query type analysis
        if user_messages:
            query_types = {
                'Price/Trading': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['price', 'token', '

# --- Enhanced Message Display Function ---
def write_message(role, content, save=True):
    """Enhanced message display with better formatting"""
    timestamp = datetime.now().strftime("%H:%M")
    icon = get_message_type_icon(content) if role == "assistant" else "👤"
    
    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            <div class="message-header">{icon} You • {timestamp}</div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:  # assistant
        st.markdown(f"""
        <div class="assistant-message">
            <div class="message-header">{icon} AuroryBot • {timestamp}</div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if save:
        st.session_state.messages.append({
            "role": role, 
            "content": content, 
            "timestamp": timestamp,
            "icon": icon
        })

# --- Enhanced Submit Handler ---
def handle_submit(message):
    """Process user message with validation and error handling"""
    # Validate input
    is_valid, error_message = validate_user_input(message)
    if not is_valid:
        write_message('assistant', f"⚠️ {error_message}")
        return
    
    # Process the message
    with st.spinner('🔍 Analyzing Aurory ecosystem data...'):
        try:
            start_time = time.time()
            response = generate_response(message)
            processing_time = time.time() - start_time
            
            # Add processing time if response took more than 2 seconds
            if processing_time > 2:
                response += f"\n\n*Analysis completed in {processing_time:.1f} seconds*"
            
            write_message('assistant', response)
            
        except Exception as e:
            error_response = f"🚨 I encountered an issue while analyzing your request. Please try rephrasing your question or contact support if the problem persists.\n\nError details: {str(e)}"
            write_message('assistant', error_response)
            st.error("An error occurred. Please try again.")

# --- Initialize Session State FIRST ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Welcome to Aurory's Economic Strategy Hub! 🚀\n\nI'm here to help you navigate the Aurory ecosystem with real-time insights on:\n• Token prices and market trends 💰\n• DAO governance and proposals 🏛️\n• NFT strategies and Neftie optimization 🎨\n• Gameplay economics and P2E strategies 🎮\n\nWhat would you like to explore first?",
            "timestamp": datetime.now().strftime("%H:%M"),
            "icon": "🎮"
        }
    ]

# --- Sidebar Menu ---
with st.sidebar:
    # Logo and title
    try:
        st.image("C:/Users/alice/OneDrive/Masaüstü/FinalCase/logo.png", width=120)
    except:
        st.write("🎮 **AURORY**")
    
    st.title("Navigation")
    page = st.radio("Choose Page:", ["💬 Chatbot", "ℹ️ About", "📊 Analytics"])
    
    st.markdown("---")
    st.markdown("### 🎯 Aurory P2E Strategy Assistant")
    st.write("Expert analysis of Aurory's game economy, token dynamics, and DAO governance.")
    
    # Display conversation stats
    display_conversation_stats()
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared! Ask me anything about Aurory's ecosystem—markets, governance, or gameplay strategies!", "timestamp": datetime.now().strftime("%H:%M"), "icon": "🎮"},
        ]
        st.rerun()
    
    if st.button("💡 Get Tips"):
        sample_questions = [
            "What's the current AURY token price trend?",
            "How do DAO proposals affect token value?",
            "What are the best Neftie strategies for P2E?",
            "Analyze recent governance decisions impact"
        ]
        tip_message = "💡 **Try asking about:**\n" + "\n".join([f"• {q}" for q in sample_questions])
        write_message('assistant', tip_message)

# --- Main Content Area ---
if page == "💬 Chatbot":
    st.title("🎮 Aurory Economic Strategy Assistant")
    st.markdown("*Your expert guide to Aurory's P2E ecosystem, tokenomics, and governance*")
    
    # Display previous messages
    for msg in st.session_state.messages:
        write_message(msg['role'], msg['content'], save=False)
    
    # Chat input
    if prompt := st.chat_input("Ask about Aurory tokens, NFTs, DAO governance, or gameplay strategies..."):
        write_message('user', prompt)
        handle_submit(prompt)

elif page == "ℹ️ About":
    st.title("About Aurory Economic Strategy Assistant")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 Mission
        This advanced AI assistant provides real-time economic intelligence for the Aurory ecosystem, helping players, investors, and DAO members make informed decisions.
        
        ### 🛠️ Capabilities
        **Market Analysis**
        - Real-time token price tracking (AURY, XAURY, NERITE, EMBER, WISDOM)
        - Historical trend analysis and predictions
        - Cross-platform price comparisons
        
        **DAO Intelligence** 
        - Governance proposal analysis
        - Voting pattern insights
        - Community sentiment tracking
        
        **Gaming Economics**
        - Neftie optimization strategies
        - P2E earning calculations
        - Guild performance metrics
        
        **Technical Infrastructure**
        - Neo4j graph database for relationship analysis
        - Vector search for semantic document retrieval
        - LangChain agents for intelligent responses
        - Real-time data integration
        
        ### 🔒 Data Sources
        - Official Aurory APIs
        - Blockchain transaction data
        - Community governance records
        - Market price feeds
        - Social sentiment analysis
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Key Features
        - 🔄 Real-time updates
        - 📈 Predictive analytics  
        - 🎯 Personalized insights
        - 🔍 Deep data analysis
        - 💬 Natural language queries
        
        ### 🚀 Getting Started
        1. Ask specific questions about Aurory
        2. Use natural language 
        3. Reference specific tokens, NFTs, or proposals
        4. Request analysis with timeframes
        
        ### 💡 Example Queries
        - "What's driving AURY price today?"
        - "Analyze the latest DAO proposal"
        - "Best Neftie builds for earning"
        - "Compare XAURY vs AURY performance"
        """)

elif page == "📊 Analytics":
    st.title("📊 Conversation Analytics")
    
    if not hasattr(st.session_state, 'messages') or len(st.session_state.messages) <= 1:
        st.info("Start chatting to see analytics here!")
        st.markdown("### 💡 What You'll See Here:")
        st.write("- Message count and interaction patterns")
        st.write("- Query type breakdown (Price, DAO, NFT, Gaming)")
        st.write("- Recent conversation activity")
        st.write("- Average question length analysis")
    else:
        # Detailed analytics
        user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in st.session_state.messages if msg['role'] == 'assistant']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Interactions", len(st.session_state.messages))
        with col2:
            st.metric("Questions Asked", len(user_messages))
        with col3:
            if user_messages:
                avg_length = sum(len(msg['content']) for msg in user_messages) / len(user_messages)
                st.metric("Avg Question Length", f"{avg_length:.0f} chars")
            else:
                st.metric("Avg Question Length", "N/A")
        
        # Query type breakdown
        if user_messages:
            st.subheader("Query Type Distribution")
            query_analysis = {
                'Token/Price Queries': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['price', 'token', '

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Aurory Economic Strategy Assistant • Built with Streamlit & LangChain • Real-time P2E Analytics
</div>
""", unsafe_allow_html=True), 'trading'])),
                'DAO/Governance': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal'])),
                'NFT/Gaming': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play']))
            }
            
            st.markdown("**Query Types:**")
            for query_type, count in query_types.items():
                if count > 0:
                    st.write(f"• {query_type}: {count}")

# --- Enhanced Message Display Function ---
def write_message(role, content, save=True):
    """Enhanced message display with better formatting"""
    timestamp = datetime.now().strftime("%H:%M")
    icon = get_message_type_icon(content) if role == "assistant" else "👤"
    
    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            <div class="message-header">{icon} You • {timestamp}</div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:  # assistant
        st.markdown(f"""
        <div class="assistant-message">
            <div class="message-header">{icon} AuroryBot • {timestamp}</div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if save:
        st.session_state.messages.append({
            "role": role, 
            "content": content, 
            "timestamp": timestamp,
            "icon": icon
        })

# --- Enhanced Submit Handler ---
def handle_submit(message):
    """Process user message with validation and error handling"""
    # Validate input
    is_valid, error_message = validate_user_input(message)
    if not is_valid:
        write_message('assistant', f"⚠️ {error_message}")
        return
    
    # Process the message
    with st.spinner('🔍 Analyzing Aurory ecosystem data...'):
        try:
            start_time = time.time()
            response = generate_response(message)
            processing_time = time.time() - start_time
            
            # Add processing time if response took more than 2 seconds
            if processing_time > 2:
                response += f"\n\n*Analysis completed in {processing_time:.1f} seconds*"
            
            write_message('assistant', response)
            
        except Exception as e:
            error_response = f"🚨 I encountered an issue while analyzing your request. Please try rephrasing your question or contact support if the problem persists.\n\nError details: {str(e)}"
            write_message('assistant', error_response)
            st.error("An error occurred. Please try again.")

# --- Initialize Session State FIRST ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Welcome to Aurory's Economic Strategy Hub! 🚀\n\nI'm here to help you navigate the Aurory ecosystem with real-time insights on:\n• Token prices and market trends 💰\n• DAO governance and proposals 🏛️\n• NFT strategies and Neftie optimization 🎨\n• Gameplay economics and P2E strategies 🎮\n\nWhat would you like to explore first?",
            "timestamp": datetime.now().strftime("%H:%M"),
            "icon": "🎮"
        }
    ]

# --- Sidebar Menu ---
with st.sidebar:
    # Logo and title
    try:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Aurory_Logo.svg/120px-Aurory_Logo.svg.png", width=120)
    except:
        st.write("🎮 **AURORY**")
    
    st.title("Navigation")
    page = st.radio("Choose Page:", ["💬 Chatbot", "ℹ️ About", "📊 Analytics"])
    
    st.markdown("---")
    st.markdown("### 🎯 Aurory P2E Strategy Assistant")
    st.write("Expert analysis of Aurory's game economy, token dynamics, and DAO governance.")
    
    # Display conversation stats
    display_conversation_stats()
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared! Ask me anything about Aurory's ecosystem—markets, governance, or gameplay strategies!", "timestamp": datetime.now().strftime("%H:%M"), "icon": "🎮"},
        ]
        st.rerun()
    
    if st.button("💡 Get Tips"):
        sample_questions = [
            "What's the current AURY token price trend?",
            "How do DAO proposals affect token value?",
            "What are the best Neftie strategies for P2E?",
            "Analyze recent governance decisions impact"
        ]
        tip_message = "💡 **Try asking about:**\n" + "\n".join([f"• {q}" for q in sample_questions])
        write_message('assistant', tip_message)

# --- Main Content Area ---
if page == "💬 Chatbot":
    st.title("🎮 Aurory Economic Strategy Assistant")
    st.markdown("*Your expert guide to Aurory's P2E ecosystem, tokenomics, and governance*")
    
    # Display previous messages
    for msg in st.session_state.messages:
        write_message(msg['role'], msg['content'], save=False)
    
    # Chat input
    if prompt := st.chat_input("Ask about Aurory tokens, NFTs, DAO governance, or gameplay strategies..."):
        write_message('user', prompt)
        handle_submit(prompt)

elif page == "ℹ️ About":
    st.title("About Aurory Economic Strategy Assistant")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 Mission
        This advanced AI assistant provides real-time economic intelligence for the Aurory ecosystem, helping players, investors, and DAO members make informed decisions.
        
        ### 🛠️ Capabilities
        **Market Analysis**
        - Real-time token price tracking (AURY, XAURY, NERITE, EMBER, WISDOM)
        - Historical trend analysis and predictions
        - Cross-platform price comparisons
        
        **DAO Intelligence** 
        - Governance proposal analysis
        - Voting pattern insights
        - Community sentiment tracking
        
        **Gaming Economics**
        - Neftie optimization strategies
        - P2E earning calculations
        - Guild performance metrics
        
        **Technical Infrastructure**
        - Neo4j graph database for relationship analysis
        - Vector search for semantic document retrieval
        - LangChain agents for intelligent responses
        - Real-time data integration
        
        ### 🔒 Data Sources
        - Official Aurory APIs
        - Blockchain transaction data
        - Community governance records
        - Market price feeds
        - Social sentiment analysis
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Key Features
        - 🔄 Real-time updates
        - 📈 Predictive analytics  
        - 🎯 Personalized insights
        - 🔍 Deep data analysis
        - 💬 Natural language queries
        
        ### 🚀 Getting Started
        1. Ask specific questions about Aurory
        2. Use natural language 
        3. Reference specific tokens, NFTs, or proposals
        4. Request analysis with timeframes
        
        ### 💡 Example Queries
        - "What's driving AURY price today?"
        - "Analyze the latest DAO proposal"
        - "Best Neftie builds for earning"
        - "Compare XAURY vs AURY performance"
        """)

elif page == "📊 Analytics":
    st.title("📊 Conversation Analytics")
    
    if len(st.session_state.messages) > 1:
        # Detailed analytics
        user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in st.session_state.messages if msg['role'] == 'assistant']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Interactions", len(st.session_state.messages))
        with col2:
            st.metric("Questions Asked", len(user_messages))
        with col3:
            avg_length = sum(len(msg['content']) for msg in user_messages) / len(user_messages) if user_messages else 0
            st.metric("Avg Question Length", f"{avg_length:.0f} chars")
        
        # Query type breakdown
        if user_messages:
            st.subheader("Query Type Distribution")
            query_analysis = {
                'Token/Price Queries': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['price', 'token', '$', 'trading', 'market'])),
                'DAO/Governance': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal', 'governance'])),
                'NFT/Gaming': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play', 'guild'])),
                'General': len(user_messages) - sum([
                    sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['price', 'token', '$', 'trading', 'market'])),
                    sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal', 'governance'])),
                    sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play', 'guild']))
                ])
            }
            
            for query_type, count in query_analysis.items():
                if count > 0:
                    percentage = (count / len(user_messages)) * 100
                    st.write(f"**{query_type}:** {count} queries ({percentage:.1f}%)")
        
        # Recent activity
        st.subheader("Recent Activity")
        for msg in st.session_state.messages[-5:]:  # Last 5 messages
            role_emoji = "👤" if msg['role'] == 'user' else msg.get('icon', '🤖')
            st.write(f"{role_emoji} **{msg['role'].title()}** ({msg.get('timestamp', 'Unknown time')}): {msg['content'][:100]}...")
    
    else:
        st.info("Start chatting to see analytics here!")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Aurory Economic Strategy Assistant • Built with Streamlit & LangChain • Real-time P2E Analytics
</div>
""", unsafe_allow_html=True), 'trading', 'market'])),
                'DAO/Governance': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal', 'governance'])),
                'NFT/Gaming': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play', 'guild'])),
            }
            
            # Calculate general queries
            specific_queries = sum(query_analysis.values())
            query_analysis['General'] = len(user_messages) - specific_queries
            
            for query_type, count in query_analysis.items():
                if count > 0:
                    percentage = (count / len(user_messages)) * 100
                    st.write(f"**{query_type}:** {count} queries ({percentage:.1f}%)")
        
        # Recent activity
        st.subheader("Recent Activity")
        recent_messages = st.session_state.messages[-5:] if len(st.session_state.messages) > 5 else st.session_state.messages[1:]  # Skip initial welcome message
        
        for msg in recent_messages:
            role_emoji = "👤" if msg['role'] == 'user' else msg.get('icon', '🤖')
            timestamp = msg.get('timestamp', 'Unknown time')
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            st.write(f"{role_emoji} **{msg['role'].title()}** ({timestamp}): {content_preview}")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Aurory Economic Strategy Assistant • Built with Streamlit & LangChain • Real-time P2E Analytics
</div>
""", unsafe_allow_html=True), 'trading'])),
                'DAO/Governance': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal'])),
                'NFT/Gaming': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play']))
            }
            
            st.markdown("**Query Types:**")
            for query_type, count in query_types.items():
                if count > 0:
                    st.write(f"• {query_type}: {count}")

# --- Enhanced Message Display Function ---
def write_message(role, content, save=True):
    """Enhanced message display with better formatting"""
    timestamp = datetime.now().strftime("%H:%M")
    icon = get_message_type_icon(content) if role == "assistant" else "👤"
    
    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            <div class="message-header">{icon} You • {timestamp}</div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:  # assistant
        st.markdown(f"""
        <div class="assistant-message">
            <div class="message-header">{icon} AuroryBot • {timestamp}</div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if save:
        st.session_state.messages.append({
            "role": role, 
            "content": content, 
            "timestamp": timestamp,
            "icon": icon
        })

# --- Enhanced Submit Handler ---
def handle_submit(message):
    """Process user message with validation and error handling"""
    # Validate input
    is_valid, error_message = validate_user_input(message)
    if not is_valid:
        write_message('assistant', f"⚠️ {error_message}")
        return
    
    # Process the message
    with st.spinner('🔍 Analyzing Aurory ecosystem data...'):
        try:
            start_time = time.time()
            response = generate_response(message)
            processing_time = time.time() - start_time
            
            # Add processing time if response took more than 2 seconds
            if processing_time > 2:
                response += f"\n\n*Analysis completed in {processing_time:.1f} seconds*"
            
            write_message('assistant', response)
            
        except Exception as e:
            error_response = f"🚨 I encountered an issue while analyzing your request. Please try rephrasing your question or contact support if the problem persists.\n\nError details: {str(e)}"
            write_message('assistant', error_response)
            st.error("An error occurred. Please try again.")

# --- Initialize Session State FIRST ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Welcome to Aurory's Economic Strategy Hub! 🚀\n\nI'm here to help you navigate the Aurory ecosystem with real-time insights on:\n• Token prices and market trends 💰\n• DAO governance and proposals 🏛️\n• NFT strategies and Neftie optimization 🎨\n• Gameplay economics and P2E strategies 🎮\n\nWhat would you like to explore first?",
            "timestamp": datetime.now().strftime("%H:%M"),
            "icon": "🎮"
        }
    ]

# --- Sidebar Menu ---
with st.sidebar:
    # Logo and title
    try:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Aurory_Logo.svg/120px-Aurory_Logo.svg.png", width=120)
    except:
        st.write("🎮 **AURORY**")
    
    st.title("Navigation")
    page = st.radio("Choose Page:", ["💬 Chatbot", "ℹ️ About", "📊 Analytics"])
    
    st.markdown("---")
    st.markdown("### 🎯 Aurory P2E Strategy Assistant")
    st.write("Expert analysis of Aurory's game economy, token dynamics, and DAO governance.")
    
    # Display conversation stats
    display_conversation_stats()
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared! Ask me anything about Aurory's ecosystem—markets, governance, or gameplay strategies!", "timestamp": datetime.now().strftime("%H:%M"), "icon": "🎮"},
        ]
        st.rerun()
    
    if st.button("💡 Get Tips"):
        sample_questions = [
            "What's the current AURY token price trend?",
            "How do DAO proposals affect token value?",
            "What are the best Neftie strategies for P2E?",
            "Analyze recent governance decisions impact"
        ]
        tip_message = "💡 **Try asking about:**\n" + "\n".join([f"• {q}" for q in sample_questions])
        write_message('assistant', tip_message)

# --- Main Content Area ---
if page == "💬 Chatbot":
    st.title("🎮 Aurory Economic Strategy Assistant")
    st.markdown("*Your expert guide to Aurory's P2E ecosystem, tokenomics, and governance*")
    
    # Display previous messages
    for msg in st.session_state.messages:
        write_message(msg['role'], msg['content'], save=False)
    
    # Chat input
    if prompt := st.chat_input("Ask about Aurory tokens, NFTs, DAO governance, or gameplay strategies..."):
        write_message('user', prompt)
        handle_submit(prompt)

elif page == "ℹ️ About":
    st.title("About Aurory Economic Strategy Assistant")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 Mission
        This advanced AI assistant provides real-time economic intelligence for the Aurory ecosystem, helping players, investors, and DAO members make informed decisions.
        
        ### 🛠️ Capabilities
        **Market Analysis**
        - Real-time token price tracking (AURY, XAURY, NERITE, EMBER, WISDOM)
        - Historical trend analysis and predictions
        - Cross-platform price comparisons
        
        **DAO Intelligence** 
        - Governance proposal analysis
        - Voting pattern insights
        - Community sentiment tracking
        
        **Gaming Economics**
        - Neftie optimization strategies
        - P2E earning calculations
        - Guild performance metrics
        
        **Technical Infrastructure**
        - Neo4j graph database for relationship analysis
        - Vector search for semantic document retrieval
        - LangChain agents for intelligent responses
        - Real-time data integration
        
        ### 🔒 Data Sources
        - Official Aurory APIs
        - Blockchain transaction data
        - Community governance records
        - Market price feeds
        - Social sentiment analysis
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Key Features
        - 🔄 Real-time updates
        - 📈 Predictive analytics  
        - 🎯 Personalized insights
        - 🔍 Deep data analysis
        - 💬 Natural language queries
        
        ### 🚀 Getting Started
        1. Ask specific questions about Aurory
        2. Use natural language 
        3. Reference specific tokens, NFTs, or proposals
        4. Request analysis with timeframes
        
        ### 💡 Example Queries
        - "What's driving AURY price today?"
        - "Analyze the latest DAO proposal"
        - "Best Neftie builds for earning"
        - "Compare XAURY vs AURY performance"
        """)

elif page == "📊 Analytics":
    st.title("📊 Conversation Analytics")
    
    if len(st.session_state.messages) > 1:
        # Detailed analytics
        user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in st.session_state.messages if msg['role'] == 'assistant']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Interactions", len(st.session_state.messages))
        with col2:
            st.metric("Questions Asked", len(user_messages))
        with col3:
            avg_length = sum(len(msg['content']) for msg in user_messages) / len(user_messages) if user_messages else 0
            st.metric("Avg Question Length", f"{avg_length:.0f} chars")
        
        # Query type breakdown
        if user_messages:
            st.subheader("Query Type Distribution")
            query_analysis = {
                'Token/Price Queries': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['price', 'token', '$', 'trading', 'market'])),
                'DAO/Governance': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal', 'governance'])),
                'NFT/Gaming': sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play', 'guild'])),
                'General': len(user_messages) - sum([
                    sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['price', 'token', '$', 'trading', 'market'])),
                    sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['dao', 'vote', 'proposal', 'governance'])),
                    sum(1 for msg in user_messages if any(word in msg['content'].lower() for word in ['nft', 'neftie', 'game', 'play', 'guild']))
                ])
            }
            
            for query_type, count in query_analysis.items():
                if count > 0:
                    percentage = (count / len(user_messages)) * 100
                    st.write(f"**{query_type}:** {count} queries ({percentage:.1f}%)")
        
        # Recent activity
        st.subheader("Recent Activity")
        for msg in st.session_state.messages[-5:]:  # Last 5 messages
            role_emoji = "👤" if msg['role'] == 'user' else msg.get('icon', '🤖')
            st.write(f"{role_emoji} **{msg['role'].title()}** ({msg.get('timestamp', 'Unknown time')}): {msg['content'][:100]}...")
    
    else:
        st.info("Start chatting to see analytics here!")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Aurory Economic Strategy Assistant • Built with Streamlit & LangChain • Real-time P2E Analytics
</div>
""", unsafe_allow_html=True)