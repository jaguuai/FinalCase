# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_neo4j import Neo4jChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage # Ekstra import

# Local imports
from llm import llm
from graph import graph
from tools.cypher import cypher_qa
from tools.vector import get_document

from utils import get_session_id

# Create a game chat chain (bu kısım zaten doğru görünüyor)
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
# --- DAO Expert Prompt ---
dao_system_message = ChatPromptTemplate.from_messages(
    [
        ("system",
         "You are the **Aurory DAO Governance Expert**, specialized in analyzing and advising on Aurory DAO proposals, voting dynamics, and community sentiment related to governance.\n"
         "Your role is to provide clear, unbiased analysis of proposals, potential impacts, quorum requirements, and voting patterns.\n\n"
         "Your knowledge domains:\n"
         "1. **DAO Governance**: Evaluate proposals (Snapshot, DAOry), participation, quorum levels, and strategic implications.\n"
         "2. **Community Sentiment**: Track and interpret user sentiment on Twitter, Snapshot, and Discord regarding governance issues.\n"
         "3. **Tokenomics (AURY/XAURY)**: Analyze how governance decisions impact AURY and XAURY token utility and distribution.\n\n"
         "Prioritize using the 'Aurory Game Information' tool for detailed proposal data and the 'Documents Search' tool for community sentiment (e.g., 'dao' or 'tweets' content_type).\n"
         "Respond with:\n"
         "- Objective analysis of proposals\n"
         "- Assessment of potential risks and benefits\n"
         "- Insights into voter behavior\n"
         "- Clear and concise language, avoiding speculation."
        ),
        ("human", "{input}"), # Bu input Agent Executor'dan gelen input ile çakışabilir, aşağıdaki düzeltmede bu mesajı çıkaracağız.
    ]
)

# --- Gaming Strategist Prompt ---
gaming_system_message = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are **Aurory Economic Strategy Assistant**, an expert agent specialized in analyzing and advising on the economy of the **Aurory Play-to-Earn game**.\n"
            "Your users include developers, players, DAO members, and community analysts.\n\n"
            "Your knowledge domains:\n"
            "1. **Tokenomics**: Analyze AURY, XAURY, NERITE, EMBER, WISDOM in terms of utility, inflation/deflation, and game function.\n"
            "2. **Earning Optimization**: Help players maximize earnings from gameplay, staking, trading, farming, and other in-game mechanics.\n"
            "3. **NFT Market**: Monitor and interpret price floors, trading volume, rarity value, and utility of Nefties/Aurorians.\n\n" # DAO Governance Insights removed from here
            "**Crucial Directive:** For any questions concerning Aurory's *tokenomics, NFT market data (prices, volume), specific game mechanics (e.g., staking, crafting, PvP), or real-time game event data that can be queried from the database*, **you MUST use the 'Aurory Game Information' tool to generate a Cypher query.**\n"
            "**Important Note on Events:** Game events are stored as `Document` nodes. When asked about 'game events', you should query `Document` nodes where `docType` is 'news_event' and the `eventType` property is present. Do NOT search for a 'GameEvent' node as it does not exist in the database schema."
            "If the information is not directly queryable from the database (e.g., subjective opinions, future predictions, or very general game lore not mapped to entities), then provide a general answer or state the limitation.\n"
            "Always include risk assessments and strategic recommendations when applicable."
        ),
        ("human", "{input}"),
    ]
)

#Safe wrapper for cypher_qa tool
def safe_cypher_invoke(query):
    """Safely invoke cypher_qa with error handling"""
    try:
        if cypher_qa is None:
            return {
                "result": "Database connection is not available. Please check Neo4j connection.",
                "generated_cypher_query": None
            }
        return cypher_qa.invoke(query)
    except Exception as e:
        return {
            "result": f"Error querying database: {str(e)}",
            "generated_cypher_query": None
        }
    
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
        func=get_document # get_document fonksiyonu doğrudan çağrılabilir bir fonksiyon olarak kalabilir
    ),
    Tool.from_function(
        name="Aurory Game Information",
        description=(
            "Answer detailed and accurate questions about the Aurory Play-to-Earn game economy by querying the Neo4j graph database.\n"
            "Use this tool for any inquiries involving tokenomics, NFT markets, DAO proposals, player strategies, or economic data within the Aurory ecosystem.\n"
            "Always rely on this tool when structured, up-to-date data from the Neo4j knowledge graph is needed."
        ),
        func=cypher_qa.invoke # cypher_qa bir zincir olduğu için .invoke() kullanıldı
    )
]


# Create chat history callback
def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)

# Agent'ın ana ReAct prompt içeriği (bu kısım doğru şekilde string olarak tanımlanmış)
# Bu, agent'ın düşünme ve araç kullanma formatını belirler.
react_agent_structure_content = """TOOLS:
------

You have access to the following tools:

{tools}

To use a tool, please use the following exact format (including the backticks and line breaks):

```
Thought: Do I need to use a tool? Yes
Action: &lt;tool name> # choose one from [{tool_names}]
Action Input: &lt;input to the tool>
Observation: &lt;tool output>
```

When you have a final answer or do not need to use any tool, reply in this exact format:

```
Thought: Do I need to use a tool? No
Final Answer: &lt;your answer here>
```

Guidelines:
-----------
- You only respond with information directly relevant to the Aurory ecosystem.
- You may suggest Cypher queries or data exploration steps if appropriate.
- If data is incomplete or speculative, you clearly mark it as such.
- Stay concise, professional, and focused on actionable insights.

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
"""

# Hata veren `agent_prompt = PromptTemplate.from_template(agent_prompt)` satırı kaldırıldı.
# `agent_prompt` artık doğrudan agent oluşturmada kullanılmayacak, içeriği kullanılacak.


# --- Agent Oluşturma ---
# Her bir agent için özel ChatPromptTemplate'ler oluşturun

# DAO Expert Agent için birleştirilmiş prompt
dao_agent_combined_prompt = ChatPromptTemplate.from_messages([
    ("system", dao_system_message.messages[0].prompt.template), # DAO'ya özel sistem mesajı
    # Human mesajı olarak ReAct yapısını ekleyin
    # Not: {input} ve {chat_history} AgentExecutor tarafından sağlanacak
    ("human", react_agent_structure_content)
])

# Gaming Strategist Agent için birleştirilmiş prompt
gaming_agent_combined_prompt = ChatPromptTemplate.from_messages([
    ("system", gaming_system_message.messages[0].prompt.template), # Gaming'e özel sistem mesajı
    # Human mesajı olarak ReAct yapısını ekleyin
    ("human", react_agent_structure_content)
])

# Agent'ları oluşturun
# --- DAO Expert Agent ---
dao_agent = create_react_agent(llm, tools, dao_agent_combined_prompt) # Birleştirilmiş prompt kullanıldı
dao_agent_executor = AgentExecutor(
    agent=dao_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True
)
dao_chat_agent = RunnableWithMessageHistory(
    dao_agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# --- Gaming Strategist Agent ---
gaming_agent = create_react_agent(llm, tools, gaming_agent_combined_prompt) # Birleştirilmiş prompt kullanıldı
gaming_agent_executor = AgentExecutor(
    agent=gaming_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True
)
gaming_chat_agent = RunnableWithMessageHistory(
    gaming_agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Agent'ları bir dictionary'de tutun
AGENTS_EXEC = {
    "dao": dao_chat_agent,
    "gaming": gaming_chat_agent,
}

# Create a handler to call the agent

def generate_response(user_input: str, agent_id: str = "gaming") -> dict: # <-- Dönüş tipini dict olarak değiştirin
    """
    Agent'ı seçilen agent_id'ye göre çağırır ve yanıt ile birlikte
    oluşturulan Cypher sorgusunu (varsa) döndürür.
    """
    selected_agent_executor = AGENTS_EXEC.get(agent_id)

    if not selected_agent_executor:
        return {"output": "Üzgünüm, seçilen agent bulunamadı. Lütfen geçerli bir agent seçin.", "generated_cypher_query": None}

    try:
        response = selected_agent_executor.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": get_session_id()}}
        )

        final_output = response.get("output", str(response))
        generated_cypher = None

        # Ara adımları kontrol ederek Cypher sorgusunu bulmaya çalışın
        intermediate_steps = response.get("intermediate_steps", [])
        for step in intermediate_steps:
            # Bir adım genellikle (AgentAction, tool_output) şeklindedir
            if isinstance(step, tuple) and len(step) == 2:
                tool_action, tool_output = step
                # "Aurory Game Information" aracı kullanıldıysa
                if tool_action.tool == "Aurory Game Information":
                    # tool_output, cypher.py'den dönen dictionary olmalı
                    if isinstance(tool_output, dict) and "generated_cypher_query" in tool_output:
                        generated_cypher = tool_output["generated_cypher_query"]
                        break # Sorguyu bulduk, döngüden çık

        return {
            "output": final_output,
            "generated_cypher_query": generated_cypher
        }

    except Exception as e:
        print(f"Agent çalıştırma hatası ({agent_id}): {e}")
        return {
            "output": f"Üzgünüm, {agent_id.replace('-', ' ').title()} agent'ı isteğinizi işlerken bir hata ile karşılaştı: {str(e)[:100]}...",
            "generated_cypher_query": None
        }