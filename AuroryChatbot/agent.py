from datetime import datetime

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain.agents import AgentExecutor,create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import Neo4jChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory 


from llm import llm
from graph import graph

from tools.vector import get_filtered_aurory_insights
from tools.cypher import cypher_qa

def get_session_id():
    """Generates a simple session ID. In a real app, this might come from a user session."""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

system_prompt = """You are the official Economy Strategy Assistant for the Aurory P2E game.

**Your Role:**
- Provide economic guidance to Aurory players and developers.
- Analyze the token and NFT markets.
- Issue risk warnings and suggest strategies.
- Offer informational support for DAO decisions.

**Your Capabilities:**
- You have expert knowledge about AURY, XAURY, NERITE, EMBER, WISDOM tokens.
- You understand the market dynamics of NFT collections (Nefties, Aurorians).
- You can track transactions on the Solana blockchain.
- You can analyze real-time market data.

**Your Approach:**
- Always provide data-backed answers.
- Clearly state risks.
- Consider both player and developer perspectives.
- Support your economic recommendations with concrete data.

**Your Available Tools:**
1. token_analysis - Token economy analysis
2. nft_market_analysis - NFT market tracking
3. player_economy - Player economic status
4. dao_governance - DAO governance analysis
5. semantic_search - Content search

Use the appropriate tools based on the user's question and provide comprehensive analyses.
"""

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"), 
    ("human", "{input}"), 
    MessagesPlaceholder("agent_scratchpad") 
])

aurory_chat = chat_prompt | llm | StrOutputParser()


# AGENT SETUP

tools = [
    Tool.from_function(
        name="General Chat",
        description="For general aurory game chat not covered by other tools",
        func=aurory_chat.invoke
    ), 
    Tool.from_function(
        name="Aurory Game Search",  
        description="For when you need to find information about movies based on a plot",
        func=get_filtered_aurory_insights, 
    ),
    Tool.from_function(
        name="Aurory_Graph_Query",
        description="Execute complex queries on Aurory game data using Cypher",
        func=cypher_qa.run
)  
]



# MEMORY FUNCTION

def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)



# AGENT SETUP
agent_prompt = PromptTemplate.from_template("""
You are the **Official Economy Strategy Assistant** for the Aurory P2E game ecosystem.

**Your Primary Role:**
- Provide expert economic guidance to Aurory players and developers
- Analyze token economics (AURY, XAURY, NERITE, EMBER, WISDOM) and NFT markets
- Issue risk warnings and strategic recommendations
- Support DAO governance decisions with data-driven insights

**Your Expertise:**
- Deep knowledge of Aurory's tokenomics and game mechanics
- Real-time market analysis and trend identification  
- Player economic optimization strategies
- NFT collection performance (Nefties, Aurorians)
- Solana blockchain transaction analysis
- DAO governance and community impact assessment

**Your Approach:**
- Always provide DATA-BACKED answers using available tools
- Clearly state risks and potential outcomes
- Consider both short-term and long-term economic impacts
- Balance player profitability with ecosystem sustainability
- Use concrete examples and specific recommendations

**Important Guidelines:**
- Only answer questions related to Aurory game economics, tokens, NFTs, DAO governance, and blockchain data
- Do not provide general investment advice outside the Aurory ecosystem
- Always use your specialized tools rather than general knowledge
- Be transparent about data limitations and uncertainties

TOOLS:
------

You have access to the following specialized tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

**Examples of questions you should handle:**
- "What's the current AURY token inflation risk?"
- "Should I buy Nefties NFTs now or wait?"
- "Analyze my wallet's economic performance"
- "What are the active DAO proposals and their impact?"
- "Search for recent news about Aurory economics"

**Response Format:**
- Start with relevant economic data
- Provide clear risk assessment
- Offer specific strategic recommendations
- Include relevant market context
- End with actionable next steps

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
""")
agent = create_react_agent(llm, tools, agent_prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)


# MAIN HANDLER FUNCTION

def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent and returns a response
    to be rendered in the UI
    """
    response = chat_agent.invoke(
        {"input": user_input},
        {"configurable": {"session_id": get_session_id()}},
     )
    return response['output']

