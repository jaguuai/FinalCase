import streamlit as st
from llm import llm
from graph import graph
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from langchain.tools import Tool

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
- Use IS NOT NULL instead of exists() to check for property existence.

Example Cypher Queries:

1 - To find game mechanics and their related documents and tokens:
```
MATCH (d:Document)-[*1..2]-(t:Token)-[*1..2]-(gt:GameToken)-[*1..2]-(gm:GameMechanic)
RETURN 
  d.documentType AS DocumentType,
  t.name AS TokenName,
  gt.name AS GameTokenName,
  gm.description AS GameMechanic
LIMIT 50
```

2 - To find tokens and game tokens discussed in tweets related to farming, yield, or rewards with high economic significance:
```
MATCH (d:Document)-[:DISCUSSES|REFERENCES|POTENTIAL_IMPACT]->(t:Token)-[:HAS_SUBTOKEN]->(gt:GameToken)
WHERE d.documentType = "tweet" 
  AND d.economicSignificance >= 3
  AND (toLower(d.content) CONTAINS "farming" 
       OR toLower(d.content) CONTAINS "yield" 
       OR toLower(d.content) CONTAINS "reward")
RETURN 
  d.content AS FarmingStrategy,
  t.name AS TokenName,
  gt.name AS GameTokenName,
  gt.symbol AS GameTokenSymbol,
  d.economicSignificance AS StrategyValue
ORDER BY d.economicSignificance DESC
LIMIT 20
```

3 - To extract game strategies from documents (tweets) mentioning strategy, tactic, earning, gameplay, or tips:
```
MATCH (d:Document)
WHERE d.documentType = "tweet" 
  AND d.economicSignificance >= 2
  AND (toLower(d.content) CONTAINS "strategy" 
       OR toLower(d.content) CONTAINS "tactic" 
       OR toLower(d.content) CONTAINS "earning" 
       OR toLower(d.content) CONTAINS "gameplay"
       OR toLower(d.content) CONTAINS "tip")
RETURN 
  d.content AS StrategyContent,
  d.economicSignificance AS Importance,
  d.retweet AS Engagement,
  d.like AS Popularity,
  d.eventType AS EventType
ORDER BY d.economicSignificance DESC, d.retweet DESC
LIMIT 20
```

4 - To find DAO proposals and related council discussions:
```
MATCH (d:Document)-[:DESCRIBES]->(p:Proposal)
OPTIONAL MATCH (c:Council)-[:MEMBER_OF]-(cm:CouncilMember)
WHERE d.documentType = "tweet" 
  AND d.economicSignificance >= 3
  AND (toLower(d.content) CONTAINS "proposal" 
       OR toLower(d.content) CONTAINS "vote" 
       OR toLower(d.content) CONTAINS "governance"
       OR toLower(d.content) CONTAINS "dao")
RETURN 
  p.title AS ProposalTitle,
  p.proposalId AS ProposalID,
  d.content AS ProposalDiscussion,
  c.name AS CouncilName,
  cm.name AS CouncilMemberName,
  d.economicSignificance AS ProposalImportance
ORDER BY d.economicSignificance DESC
LIMIT 20
```

5 - To find wallet transactions and NFT activities:
```
MATCH (w:Wallet)-[:PERFORMED]->(tx:Transaction)
OPTIONAL MATCH (w)-[:BUYS|SELLS]->(nft:NftItem)
WHERE w.userLevel IS NOT NULL
RETURN 
  w.address AS WalletAddress,
  w.userLevel AS UserLevel,
  count(DISTINCT tx) AS TransactionCount,
  count(DISTINCT nft) AS NFTCount,
  w.amount AS WalletBalance
ORDER BY w.userLevel DESC, count(tx) DESC
LIMIT 20
```

Schema:
{schema}

Question:
{question}
"""


cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

# Custom function to clean generated Cypher
def clean_generated_cypher(generated_cypher):
    """Clean the generated cypher by removing explanatory text"""
    lines = generated_cypher.strip().split('\n')
    cypher_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and explanatory text
        if not line:
            continue
        # Skip lines that look like explanations
        if (line.startswith('The ') or 
            line.startswith('According to') or 
            line.startswith('Based on') or
            line.startswith('Here is') or
            line.startswith('This query') or
            'correct' in line.lower() or
            'schema' in line.lower() or
            line.startswith('```') or
            line.startswith('Cypher Query:')):
            continue
        # If line starts with a Cypher keyword, we're good
        cypher_keywords = ['MATCH', 'RETURN', 'WHERE', 'WITH', 'ORDER', 'LIMIT', 'SKIP', 'UNION', 'CREATE', 'MERGE', 'DELETE', 'DETACH', 'SET', 'REMOVE', 'OPTIONAL', 'UNWIND', 'CALL']
        if any(line.upper().startswith(keyword) for keyword in cypher_keywords):
            cypher_lines.append(line)
        elif cypher_lines:  # If we already have cypher lines, this might be a continuation
            cypher_lines.append(line)
    
    # Join the cleaned cypher
    cleaned_cypher = '\n'.join(cypher_lines)
    
    if not cleaned_cypher.strip():
        # Fallback: try to find cypher in the original text
        import re
        cypher_match = re.search(r'(MATCH.*?)(?:\n\n|\Z)', generated_cypher, re.DOTALL | re.IGNORECASE)
        if cypher_match:
            cleaned_cypher = cypher_match.group(1).strip()
        else:
            cleaned_cypher = generated_cypher.strip()
    
    return cleaned_cypher

# Create a custom GraphCypherQAChain with better error handling for newer LangChain versions
class CustomGraphCypherQAChain(GraphCypherQAChain):
    def _call(self, inputs, run_manager=None):
        try:
            # Get the generated cypher using invoke instead of run
            cypher_input = {
                "question": inputs[self.input_key], 
                "schema": self.graph.schema
            }
            
            # Use invoke instead of run for newer LangChain versions
            if hasattr(self.cypher_generation_chain, 'invoke'):
                generated_cypher = self.cypher_generation_chain.invoke(cypher_input)
            else:
                generated_cypher = self.cypher_generation_chain.run(**cypher_input)
            
            # Handle different return types
            if isinstance(generated_cypher, dict):
                generated_cypher = generated_cypher.get('text', str(generated_cypher))
            elif not isinstance(generated_cypher, str):
                generated_cypher = str(generated_cypher)
            
            # Clean the generated cypher
            cleaned_cypher = clean_generated_cypher(generated_cypher)
            
            print(f"Original generated cypher: {generated_cypher}")
            print(f"Cleaned cypher: {cleaned_cypher}")
            
            # Execute the cleaned cypher
            context = self.graph.query(cleaned_cypher)[: self.top_k]
            
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
            
            return {self.output_key: result}
            
        except Exception as e:
            print(f"Error in cypher execution: {e}")
            return {self.output_key: f"I encountered an error while querying the database: {str(e)}. Please try rephrasing your question."}

cypher_qa = CustomGraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt,
    allow_dangerous_requests=True
)