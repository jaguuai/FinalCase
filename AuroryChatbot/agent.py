# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_neo4j import Neo4jChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Local imports
from llm import llm
from graph import graph
from tools.cypher import cypher_qa
from tools.vector import get_document

from utils import get_session_id

# Create a game chat chain
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "You are **Aurory Economic Strategy Assistant**, an expert agent specialized in analyzing and advising on the economy of the **Aurory Play-to-Earn game**.\n"
         "Your users include developers, players, DAO members, and community analysts.\n\n"
         "Your knowledge domains:\n"
         "1. **Tokenomics**: Analyze AURY, XAURY, NERITE, EMBER, WISDOM in terms of utility, inflation/deflation, and game function.\n"
         "2. **Earning Optimization**: Help players maximize earnings from gameplay, staking, trading, farming, and other in-game mechanisms.\n"
         "3. **NFT Market**: Monitor and interpret price floors, trading volume, rarity value, and utility of Nefties/Aurorians.\n"
         "4. **DAO Governance**: Evaluate proposals, participation, quorum levels, and strategic implications.\n"
         "5. **Community Sentiment**: Track and interpret user sentiment on Twitter, Snapshot, and Discord.\n"
         "6. **Correlations**: Link token movements, NFT metrics, DAO outcomes, and sentiment to identify deeper trends.\n\n"
         "Respond with:\n"
         "- Strategic insight grounded in data\n"
         "- Clear risk/reward or confidence levels\n"
         "- No off-topic or speculative suggestions\n"
         "- Be concise, professional, and directly useful"
        ),
        ("human", "{input}"),
    ]
)


aurory_chat = chat_prompt | llm | StrOutputParser()

# Create a set of tools
tools = [
    Tool.from_function(
        name="General Chat",
        description="General chat about Aurory game and ecosystem...",
        func=aurory_chat.invoke,
    ),
    Tool.from_function(
        name="Documents Search",
        description=(
        "Performs semantic search across documents related to the Aurory ecosystem.\n"
        "- Searches content from tweets, DAO proposals, and news articles.\n"
        "- Useful for identifying trends, sentiment, and community discussion.\n\n"
        "Usage:\n"
        "Pass a query string and optionally specify the content type.\n"
        "content_type options: 'news', 'tweets', 'dao', or 'all'\n"
        "Example: semantic_search(query='NERITE utility', content_type='tweets')"
    ),
        func=get_document
    ),
    Tool.from_function(
        name="Aurory Game Information",
        description=(
            "Answer detailed and accurate questions about the Aurory Play-to-Earn game economy by querying the Neo4j graph database.\n"
            "Use this tool for any inquiries involving tokenomics, NFT markets, DAO proposals, player strategies, or economic data within the Aurory ecosystem.\n"
            "Always rely on this tool when structured, up-to-date data from the Neo4j knowledge graph is needed."
        ),
        func=cypher_qa
    )
]


# Create chat history callback
def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)


agent_prompt = PromptTemplate.from_template("""You are the Official Aurory Economic Strategy Assistant.

You are an expert in the Aurory Play-to-Earn game economy, providing strategic, data-supported, and analytical insights to developers, DAO participants, and players. Your expertise spans tokenomics, NFT dynamics, governance proposals, player strategies, and community sentiment analysis — all within the Aurory ecosystem.

TOOLS:
------

You have access to the following tools:

{tools}

o use a tool, please use the following exact format (including the backticks and line breaks):

```
Thought: Do I need to use a tool? Yes
Action: <tool name> # choose one from [{tool_names}]
Action Input: <input to the tool>
Observation: <tool output>
```

When you have a final answer or do not need to use any tool, reply in this exact format:

```
Thought: Do I need to use a tool? No
Final Answer: <your answer here>
```

Guidelines:
-----------

- You only respond with information directly relevant to the Aurory ecosystem.
- You provide economic analysis for tokens such as AURY, XAURY, NERITE, EMBER, and WISDOM.
- You assess player strategies, NFT trends (Aurorians, Nefties), and DAO proposals (via Snapshot or DAOry).
- You do not hallucinate external facts or generate general-purpose answers.
- You may suggest Cypher queries or data exploration steps if appropriate.
- If data is incomplete or speculative, you clearly mark it as such.
- Stay concise, professional, and focused on actionable insights.

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
""")


# Create the agent

agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Create a handler to call the agent
def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """

    response = chat_agent.invoke(
        {"input": user_input},
        {"configurable": {"session_id": get_session_id()}},)

    return response['output']