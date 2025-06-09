# Optimized version of cypher.py with simplified schema

import streamlit as st
from llm import llm
from graph import graph
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from langchain.tools import Tool
from langchain.callbacks.manager import CallbackManagerForChainRun

# Simplified schema definition instead of full schema
SIMPLIFIED_SCHEMA = """
Nodes:
- Document (properties: 
    * content (text content)
    * docType (tweet, news , dao_proposal)
    * title (document title)
    * source (source URL or identifier)
    * timestamp (creation/publication time)
    * influenceScore (numeric influence score)
    * eventType (type of event)
    * economicSignificance (economic impact assessment)
    * socialImpact (social media impact metrics)
    * tweet_id (for Twitter documents)
    * proposalId (for DAO proposal documents)
    )
- Token (properties: name, symbol, coinType, volume24hUsd, percentChange24h, marketCapUsd)
- Wallet (properties: address, amount, userLevel, transactionCount)
- Transaction (properties: signature, timestamp, fee, slot)
- NftItem (properties: id, priceSOL, timestamp, status, collection)
- Proposal (properties: title, proposalId,status)
- Council (properties: description, electionCycle)
- GameMechanic (properties: name, description)
- CommunityMember (properties: twitter, name, role)

Relationships:
- Document-[:DISCUSSES|REFERENCES|POTENTIAL_IMPACT]->Token
- Document-[:MENTIONS]->GameMechanic  
- Document-[:ABOUT]->NftItem
- Document-[:DESCRIBES]->Proposal
- Wallet-[:HOLDS]->Token 
- Wallet-[:SELLS]->NftItem 
- Wallet-[:BUYS]->NftItem 
- Wallet-[:PERFORMED]->Transaction
- Token-[:HAS_SUBTOKEN]->GameToken
- Token-[:HAS_LIFECYCLE]->GameMechanic
- GameMechanic-[:REQUIRES]->GameToken
- GameMechanic-[:REWARDS]->GameToken
- GameMechanic-[:CONSUMES]->GameToken
- Council-[:MEMBER_OF]->CommunityMember
- CommunityMember-[:OWNS]->Wallet
"""

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
-When a question involves event, filter Document nodes by `docType` properties 'news'.
-When a question involves "player" or "user" actions, treat them as Wallet nodes. 

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

class CustomGraphCypherQAChain(GraphCypherQAChain):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure all required attributes are properly set
        if not hasattr(self, 'llm') and 'llm' in kwargs:
            self.llm = kwargs['llm']

    def _call(
        self,
        inputs: dict[str, str],
        run_manager = None,
    ) -> dict[str, str]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        
        try:
            # Use simplified schema instead of full schema
            chain_inputs = {
                "question": inputs[self.input_key],
                "schema": SIMPLIFIED_SCHEMA  # Use our simplified schema
            }

            # Generate the Cypher query with robust error handling
            try:
                if hasattr(self.cypher_generation_chain, 'invoke'):
                    intermediate_result = self.cypher_generation_chain.invoke(
                        chain_inputs,
                        callbacks=callbacks
                    )
                    # Handle different return types robustly
                    if isinstance(intermediate_result, dict):
                        cleaned_cypher = intermediate_result.get("text", intermediate_result.get("output", str(intermediate_result)))
                    elif isinstance(intermediate_result, str):
                        cleaned_cypher = intermediate_result
                    else:
                        # Handle other types (like AIMessage objects)
                        cleaned_cypher = getattr(intermediate_result, 'content', str(intermediate_result))
                else:
                    cleaned_cypher = self.cypher_generation_chain.run(
                        question=chain_inputs["question"],
                        schema=chain_inputs["schema"],
                        callbacks=callbacks
                    )
            except Exception as chain_error:
                print(f"Cypher generation error: {chain_error}")
                return {
                    self.output_key: f"Failed to generate Cypher query: {str(chain_error)}",
                    "generated_cypher_query": None
                }

            # Clean the cypher query
            if "```cypher" in cleaned_cypher:
                cleaned_cypher = cleaned_cypher.split("```cypher")[1].split("```")[0].strip()
            elif "```" in cleaned_cypher:
                cleaned_cypher = cleaned_cypher.split("```")[1].strip()

            if self.verbose:
                _run_manager.on_text(f"Generated Cypher: {cleaned_cypher}\n", verbose=self.verbose)
            
            # Execute the cleaned cypher with proper error handling
            try:
                # CRITICAL FIX: Check if graph is string (connection error)
                if isinstance(self.graph, str):
                    raise ValueError(f"Graph connection failed: {self.graph}")
                
                # Check if graph has required methods
                if not hasattr(self.graph, 'query') or not callable(self.graph.query):
                    raise AttributeError(f"Graph object doesn't have a callable query method")
                
                # Execute the query
                context = self.graph.query(cleaned_cypher)[: self.top_k]
                    
            except Exception as query_error:
                print(f"Query execution error: {query_error}")
                # Return detailed error information
                return {
                    self.output_key: f"Database query failed: {str(query_error)}. Please check your Neo4j connection and try again.",
                    "generated_cypher_query": cleaned_cypher
                }

            if run_manager:
                run_manager.on_text("Generated Cypher:", end="\n", verbose=self.verbose)
                run_manager.on_text(cleaned_cypher, color="green", end="\n", verbose=self.verbose)
                run_manager.on_text("Full Context:", end="\n", verbose=self.verbose)
                run_manager.on_text(str(context), color="green", end="\n", verbose=self.verbose)
            
            # Use invoke for qa_chain as well
            qa_input = {"question": inputs[self.input_key], "context": context}
            if hasattr(self.qa_chain, 'invoke'):
                result = self.qa_chain.invoke(qa_input)
            else:
                result = self.qa_chain.run(**qa_input)
            
            # Handle different return types for result
            if isinstance(result, dict):
                result = result.get('text', str(result))
            
            return {
                self.output_key: result,
                "generated_cypher_query": cleaned_cypher
            }
            
        except Exception as e:
            print(f"Error in cypher execution: {e}")
            return {
                self.output_key: f"I encountered an error while querying the database: {str(e)}. Please check your Neo4j connection.",
                "generated_cypher_query": None
            }


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

# Alternative approach: Get schema dynamically but filter it
def get_filtered_schema(graph_obj):
    """Get only essential schema information"""
    try:
        # Get basic node labels and relationship types
        nodes_query = "CALL db.labels() YIELD label RETURN collect(label) as labels"
        relationships_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types"
        
        node_labels = graph_obj.query(nodes_query)[0]['labels']
        rel_types = graph_obj.query(relationships_query)[0]['types']
        
        # Create a minimal schema representation
        schema_info = f"""
Node Labels: {', '.join(node_labels)}
Relationship Types: {', '.join(rel_types)}

Key Properties per Node:
- Document: content, docType, influenceScore , eventType
- Token: name, symbol, volume24hUsd, marketCapUsd  
- Wallet: address, amount, userLevel
- Transaction: signature, timestamp, fee
- NftItem: priceSOL, timestamp, status
"""
        return schema_info
    except:
        return SIMPLIFIED_SCHEMA

# Chain initialization with proper error handling
if validate_graph_connection(graph):
    try:
        cypher_qa = CustomGraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=CYPHER_GENERATION_PROMPT,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
        )
        print("✅ Cypher QA Chain initialized successfully")
    except Exception as e:
        st.error(f"Failed to initialize Cypher QA chain: {str(e)}")
        print(f"Chain initialization error: {e}")
        cypher_qa = None
else:
    st.error("Cannot initialize Cypher QA chain due to graph connection issues")
    cypher_qa = None