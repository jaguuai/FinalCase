import streamlit as st
from utils import write_message
from agent import generate_response # Import get_economic_summary

# Page Config
st.set_page_config("Aurory", page_icon="🎮")

# Set up Session State
if "messages" not in st.session_state:
    # Call get_economic_summary() to get the initial comprehensive overview
    # initial_summary = get_economic_summary()
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me anything, Seeker—markets, votes, or Neftie power!"},
    ]

# Submit handler
def handle_submit(message):
    """
    Submit handler:

    You will modify this method to talk with an LLM and provide
    context using data from Neo4j.
    """

    # Handle the response
    with st.spinner('Thinking...'):
        # Call the agent
        response = generate_response(message)
        write_message('assistant', response)

# Display messages in Session State
for message in st.session_state.messages:
    write_message(message['role'], message['content'], save=False)


# Handle any user input
if prompt := st.chat_input("Ask me anything, Seeker—markets, votes, or Neftie power!"):
    # Display user message in chat message container
    write_message('user', prompt)

    # Generate a response
    handle_submit(prompt)