import streamlit as st
from llm import llm
from graph import graph
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j developer specialized in the Aurory Play-to-Earn game ecosystem.
Your task is to translate user questions into efficient Cypher queries that strictly follow the provided schema and relationship types.

Guidelines:
- Do not wrap the generated Cypher query in quotation marks.
- Return only relevant properties, never entire nodes or embedding data.
- Use case-insensitive matching when filtering by token names, symbols, or proposal titles.
- When matching names starting with "the", rearrange to "name, the" (e.g., "the aurory" → "aurory, the").
- Use sensible LIMITs (default to 20) for query performance.
- Use OPTIONAL MATCH to safely handle missing relationships or properties.
- Alias relationships if referencing their properties (e.g., [r:HOLDS] if using r.amount).
- When aggregating transfers or movements, group results by wallet address and asset name, if applicable.
- Return only properties relevant to the user's question (e.g., wallet address, amount, token name, timestamp).
- Interpret intents like "move", "transfer", or "send" using the 'PERFORMED' relationship between Wallet and Transaction nodes.
- Use IS NOT NULL instead of EXISTS to check for property existence.
- **When a question implies "social media", "tweets", or "news", filter Document nodes by `docType` properties like 'tweet', 'news'. For "proposals", "governance", or "DAO discussions", filter by `docType = 'dao_proposal'`.**
- When a question involves event, filter Document nodes by `docType` properties 'news'.
- When a question involves "player" or "user" actions, treat them as Wallet nodes.
- Avoid returning embedding properties or large text fields unless specifically requested.

Example Cypher Queries:

1 - To find documents with high influence scores:
```
MATCH (d:Document)-[:DISCUSSES|REFERENCES|POTENTIAL_IMPACT]->(t:Token)
WHERE d.influenceScore IS NOT NULL
RETURN d.content, d.influenceScore, t.name
ORDER BY d.influenceScore DESC
LIMIT 5
```

2 - To find game mechanics mentioned in documents:
```
MATCH (d:Document)-[:MENTIONS]->(gm:GameMechanic)
RETURN d.content, gm.name, gm.description
LIMIT 10
```

Schema:
{schema}

Question:
{question}
"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    template=CYPHER_GENERATION_TEMPLATE,
    input_variables=["schema", "question"]
)

def validate_graph_connection(graph_obj):
    """Check if graph object is valid Neo4j connection"""
    if isinstance(graph_obj, str):
        st.error(f"❌ Graph connection error: {graph_obj}")
        return False
    try:
        # Simple validation query
        graph_obj.query("RETURN 1 AS test")
        return True
    except Exception as e:
        st.error(f"🔌 Neo4j Connection Failed: {str(e)}")
        return False

# Chain initialization with LangChain's built-in schema
if validate_graph_connection(graph):
    try:
        cypher_qa = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=CYPHER_GENERATION_PROMPT,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
        )
        print("✅ Cypher QA Chain initialized successfully with built-in schema")
    except Exception as e:
        st.error(f"Failed to initialize Cypher QA chain: {str(e)}")
        print(f"Chain initialization error: {e}")
        cypher_qa = None
else:
    st.error("Cannot initialize Cypher QA chain due to graph connection issues")
    cypher_qa = None