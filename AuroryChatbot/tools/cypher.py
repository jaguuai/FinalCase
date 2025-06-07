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
- Use only the relationship types and properties explicitly defined in the schema below.
- Avoid using properties or relationships not present in the schema.
- Do not wrap the generated Cypher query in quotation marks.
- Do not return entire nodes or embedding data; return only relevant properties.
- Use case-insensitive text matching when filtering by token names, symbols, or proposal titles.
- When matching names that start with 'the', rearrange them to 'name, the' (e.g., "the aurory" → "aurory, the").
- Use sensible LIMITs (default 20) to optimize performance.
- Use OPTIONAL MATCH to safely handle missing relationships or properties.
- Convert dates like 'today', 'last 24 hours', or specific days into Neo4j datetime filters.
- When using Unix timestamps (epoch seconds), multiply by 1000 and use datetime({{epochMillis: ...}}).
- Always alias relationships if you reference their properties (e.g., [r:HOLDS] if using r.amount).
- When aggregating movements or transfers, group by wallet address and asset name if applicable.
- Return only the properties relevant to the user's question (e.g., wallet address, amount, token name, timestamp).
- When interpreting user intent like "move", "transfer", or "send", use the 'SENT' relationship between Wallet and Transaction nodes.
- Use IS NOT NULL instead of exists() function for property existence checks.

Example Cypher Statements:


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