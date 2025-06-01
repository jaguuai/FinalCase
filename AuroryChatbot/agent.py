import os
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, StrOutputParser
from langchain.tools import BaseTool, Tool 
from langchain.agents import AgentExecutor, create_openai_functions_agent 
from langchain.memory import ConversationBufferWindowMemory 
from langchain_neo4j import Neo4jChatMessageHistory, Neo4jVector 
from langchain_core.runnables.history import RunnableWithMessageHistory 

from llm import llm, embeddings
from graph import graph

def get_session_id():
    """Generates a simple session ID. In a real app, this might come from a user session."""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# =============================================================================
# TOOLS DEFINITION - 5 Ana Agent İçin Araçlar (English Descriptions)
# =============================================================================

class TokenAnalysisTool(BaseTool):
    """Tool for analyzing tokenomics and inflation."""
    name: str = "token_analysis" 
    description: str = """Analyzes the token economy of the Aurory game.
    Provides insights into AURY, XAURY, NERITE, EMBER, WISDOM tokens regarding:
    - Supply/demand status
    - Inflation/deflation risk
    - Price trends
    - Staking and burning rates
    Usage: token_analysis(analysis_type: 'inflation'|'supply'|'price'|'staking')"""
    
    def _run(self, analysis_type: str = "general") -> str:
        query = """
        MATCH (t:Token)
        OPTIONAL MATCH (t)-[r]-(w:Wallet)
        OPTIONAL MATCH (t)-[:HAS_SUBTOKEN]->(gt:GameToken)
        OPTIONAL MATCH (gm:GameMechanic)-[:REWARDS|:REQUIRES|:CONSUMES]->(gt)
        WITH t, count(DISTINCT w) as holder_count,
             collect(DISTINCT gt.name) as game_tokens,
             collect(DISTINCT gm.type) as mechanics
        RETURN t.name as token_name, 
               t.usd as current_price,
               t.percentChange24h as price_change,
               holder_count,
               game_tokens,
               mechanics,
               t.marketCapUsd as market_cap_usd
        ORDER BY market_cap_usd DESC
        """
        
        result = graph.query(query)
        
        analysis = f"🔍 **Token Economy Analysis** ({analysis_type})\n\n"
        
        if not result:
            return "No token data available for analysis."

        for record in result:
            token_name = record['token_name']
            price = record['current_price'] if record['current_price'] is not None else 0.0
            change = record['price_change'] if record['price_change'] is not None else 0.0
            holders = record['holder_count'] if record['holder_count'] is not None else 0
            
            analysis += f"**{token_name}**\n"
            analysis += f"• Current Price: ${price:.6f}\n"
            analysis += f"• 24h Change: {change:.2f}%\n"
            analysis += f"• Holder Count: {holders}\n"
            
            if record['game_tokens']:
                analysis += f"• Sub-Tokens: {', '.join(record['game_tokens'])}\n"
            
            if analysis_type == "inflation":
                if change < -10:
                    analysis += "⚠️ **HIGH INFLATION RISK** - Immediate intervention recommended\n"
                elif change < -5:
                    analysis += "⚡ Moderate inflation risk\n"
                else:
                    analysis += "✅ Stable situation\n"
            
            analysis += "\n"
            
        return analysis

class NFTMarketTool(BaseTool):
    """Tool for NFT market analysis and floor price tracking."""
    name: str = "nft_market_analysis" 
    description: str = """Performs market analysis for Aurory NFT collections:
    - Floor price trends
    - Trade volume analysis
    - Mint rate tracking
    - Collection performance
    Usage: nft_market_analysis(metric: 'floor'|'volume'|'mint'|'performance')"""
    
    def _run(self, metric: str = "general") -> str:
        query = """
        MATCH (c:Collection)
        OPTIONAL MATCH (n:NFTItem)-[:BELONGS_TO]->(c)
        RETURN c.name as collection_name,
               c.floorPriceSOL as floor_price,
               c.tradeVolumeSOL as volume,
               c.mintRateEventsPerSec as mint_rate,
               c.lastMinttime as last_mint,
               count(n) as total_items,
               avg(n.priceSOL) as avg_price
        ORDER BY c.tradeVolumeSOL DESC
        """
        
        result = graph.query(query)
        
        analysis = f"🎨 **NFT Market Analysis** ({metric})\n\n"

        if not result:
            return "No NFT collection data available for analysis."
        
        for record in result:
            collection = record['collection_name']
            floor = record['floor_price'] if record['floor_price'] is not None else 0.0
            volume = record['volume'] if record['volume'] is not None else 0.0
            mint_rate = record['mint_rate'] if record['mint_rate'] is not None else 0.0
            
            analysis += f"**{collection}**\n"
            analysis += f"• Floor Price: {floor:.3f} SOL\n"
            analysis += f"• Trade Volume: {volume:.2f} SOL\n"
            analysis += f"• Mint Rate: {mint_rate:.4f} events/sec\n"
            
            if metric == "floor":
                if floor < 0.1:
                    analysis += "🔴 **LOW FLOOR PRICE** - NFT inflation risk\n"
                elif floor > 1.0:
                    analysis += "🟢 Healthy floor price\n"
                else:
                    analysis += "🟡 Moderate floor price\n"
            
            analysis += "\n"
            
        return analysis

class PlayerEconomyTool(BaseTool):
    """Tool for player economic status and earnings analysis."""
    name: str = "player_economy"
    description: str = """Analyzes the economic status of players:
    - Earnings/expenditure analysis
    - Risk assessments
    - Strategy recommendations
    Note: Detailed NFT bought/sold counts are not available with current data.
    Usage: player_economy(wallet_address: str, analysis: 'earnings'|'risk')""" # Removed 'roi' and 'bought/sold' specific analysis
    
    def _run(self, wallet_address: str = None, analysis: str = "general") -> str:
        if wallet_address:
            query = """
            MATCH (w:Wallet {address: $address})
            OPTIONAL MATCH (w)-[tx_rel:SENT]->(tx_node:Transaction) 
            // BOUGHT and SOLD relationships are not in the provided CSV, so removed direct counting
            // OPTIONAL MATCH (w)-[:BOUGHT]->(n_bought:NFTItem)
            // OPTIONAL MATCH (w)-[:SOLD]->(n_sold:NFTItem)
            
            // To get NFT items held, we might need a specific 'HOLDS_NFT' relationship or similar
            // For now, focusing on token amount and general transactions
            
            RETURN w.address as wallet,
                   w.amount as token_amount,
                   w.userLevel as level,
                   count(DISTINCT tx_node) as transaction_count
                   // nfts_bought_count and nfts_sold_count removed due to CSV limitations
            """
            result = graph.query(query, {"address": wallet_address}) 
        else:
            query = """
            MATCH (w:Wallet)
            OPTIONAL MATCH (w)-[tx_rel:SENT]->(tx_node:Transaction) 
            // BOUGHT and SOLD relationships are not in the provided CSV, so removed direct counting
            // OPTIONAL MATCH (w)-[:BOUGHT]->(n_bought:NFTItem)
            // OPTIONAL MATCH (w)-[:SOLD]->(n_sold:NFTItem)
            
            RETURN w.userLevel as level,
                   avg(w.amount) as avg_tokens,
                   count(DISTINCT tx_node) as transaction_count
                   // nfts_bought_count and nfts_sold_count removed due to CSV limitations
            ORDER BY level DESC
            LIMIT 10
            """
            result = graph.query(query)
            
        analysis = f"👤 **Player Economy Analysis** ({analysis})\n\n"
        
        if not result:
            return "No player data available for analysis or wallet not found."

        for record in result:
            if wallet_address:
                level = record['level'] if record['level'] is not None else 0
                tokens = record['token_amount'] if record['token_amount'] is not None else 0
                transaction_count = record['transaction_count'] if record['transaction_count'] is not None else 0
                
                analysis += f"**Wallet:** {wallet_address[:8]}...\n"
                analysis += f"• Level: {level}\n"
                analysis += f"• Token Balance: {tokens:,.0f}\n"
                analysis += f"• Total Transactions (SENT): {transaction_count}\n"
                # Removed NFT bought/sold counts as they are not supported by the current CSV
                
                # Simplified risk analysis based on general transaction volume or token balance
                if analysis == "risk":
                    if tokens < 1000 and transaction_count < 10:
                        analysis += "🔴 **LOW ACTIVITY/RISK** - Potentially inactive or new player.\n"
                    elif tokens > 10000 and transaction_count > 100:
                        analysis += "🟢 **HIGH ACTIVITY/ENGAGEMENT** - Significant participation.\n"
                    else:
                        analysis += "🟡 Moderate activity level.\n"
            else:
                level = record['level'] if record['level'] is not None else 0
                avg_tokens = record['avg_tokens'] if record['avg_tokens'] is not None else 0
                transaction_count = record['transaction_count'] if record['transaction_count'] is not None else 0
                
                analysis += f"• Level {level}: Avg {avg_tokens:,.0f} tokens, {transaction_count} Total Transactions\n" 
        
        # Add a note about data limitations for the user
        analysis += "\n*Note: Detailed NFT purchase/sale data is not available with the current graph schema and provided CSVs.*"
        
        return analysis

class DAOGovernanceTool(BaseTool):
    """Tool for DAO governance analysis and voting tracking."""
    name: str = "dao_governance" 
    description: str = """Analyzes DAO decisions and governance:
    - Active proposals
    - Voting participation
    - Council activity
    - Community impacts
    Usage: dao_governance(focus: 'proposals'|'voting'|'council'|'impact')"""
    
    def _run(self, focus: str = "general") -> str:
        query = """
        MATCH (p:Proposal)
        OPTIONAL MATCH (d:Document)-[:DESCRIBES]->(p)
        OPTIONAL MATCH (c:Council)-[:MEMBER_OF]->(w:Wallet)
        RETURN p.proposalId as proposal_id, 
               p.title as title,
               count(DISTINCT d) as document_count,
               collect(DISTINCT c.name) as council_members
        ORDER BY p.proposalId DESC
        """
        
        result = graph.query(query)
        
        analysis = f"🏛️ **DAO Governance Analysis** ({focus})\n\n"

        if not result:
            return "No DAO proposal data available for analysis."
        
        for record in result:
            prop_id = record['proposal_id']
            title = record['title'] if record['title'] is not None else "No Title"
            doc_count = record['document_count'] if record['document_count'] is not None else 0
            
            analysis += f"**Proposal #{prop_id}**\n"
            analysis += f"• Title: {title}\n"
            analysis += f"• Document Count: {doc_count}\n"
            
            if focus == "impact":
                if "token" in title.lower() or "economic" in title.lower():
                    analysis += "💰 **HIGH ECONOMIC IMPACT**\n"
                elif "governance" in title.lower():
                    analysis += "⚖️ Governance impact\n"
                else:
                    analysis += "📋 General impact\n"
            
            analysis += "\n"
            
        return analysis

class SemanticSearchTool(BaseTool):
    """Tool for vector-based semantic search."""
    name: str = "semantic_search" 
    description: str = """Performs semantic search about the Aurory ecosystem:
    - Searches news, tweets, DAO documents
    - Finds similar content
    - Helps with trend analysis
    Usage: semantic_search(query: str, content_type: 'news'|'tweets'|'dao'|'all')"""
    
    def _run(self, query: str, content_type: str = "all") -> str:
        vector_search = Neo4jVector.from_existing_index(
            embeddings,
            graph=graph,
            index_name="aurory_docs", 
            node_label="Document",
            text_node_property="content", 
            embedding_node_property="embedding" 
        )
        
        results = vector_search.similarity_search(query, k=3)
        
        analysis = f"🔍 **Semantic Search Results**\nQuery: '{query}'\n\n"
        
        if not results:
            return "No relevant documents found for your query."

        for i, doc in enumerate(results, 1):
            content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            source = doc.metadata.get('source', 'Unknown')
            doc_type = doc.metadata.get('doc_type', 'General') 
            
            if content_type != "all" and doc_type != content_type:
                continue 

            analysis += f"**Result {i}** ({doc_type})\n"
            analysis += f"• Source: {source}\n"
            analysis += f"• Content: {content}\n\n"
            
        return analysis

# =============================================================================
# AGENT SETUP
# =============================================================================

def get_memory(session_id: str):
    """Returns a Neo4jChatMessageHistory instance for the given session ID."""
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)

tools = [
    TokenAnalysisTool(),
    DAOGovernanceTool(),
    SemanticSearchTool()
]

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

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"), 
    ("human", "{input}"), 
    MessagesPlaceholder("agent_scratchpad") 
])

agent = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True, 
    handle_parsing_errors=True, 
    max_iterations=5 
)

chat_agent_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_memory, 
    input_messages_key="input",
    history_messages_key="chat_history",
)

# =============================================================================
# CHAT HISTORY CALLBACK (for long-term persistence in Neo4j)
# =============================================================================

def save_chat_history(session_id: str, message: dict):
    """Saves chat history to Neo4j."""
    query = """
    MERGE (s:ChatSession {id: $session_id})
    CREATE (m:Message {
        role: $role,
        content: $content,
        timestamp: datetime()
    })
    CREATE (s)-[:HAS_MESSAGE]->(m)
    """
    
    try:
        graph.query(query, {
            "session_id": session_id,
            "role": message["role"],
            "content": message["content"]
        })
    except Exception as e:
        print(f"Error saving chat history to Neo4j: {e}")


# =============================================================================
# MAIN HANDLER (for external interaction)
# =============================================================================

def generate_response(message: str, session_id: str = None) -> str:
    """
    Main chat handler function.
    Calls the Conversational agent and returns a response.
    """
    try:
        if not session_id:
            session_id = get_session_id()
        
        save_chat_history(session_id, {"role": "user", "content": message})
        
        response = chat_agent_with_history.invoke(
            {"input": message},
            {"configurable": {"session_id": session_id}}, 
        )
        
        agent_output = response["output"]
        save_chat_history(session_id, {"role": "assistant", "content": agent_output})
        
        return agent_output
        
    except Exception as e:
        error_msg = f"Sorry, an error occurred: {str(e)}"
        print(f"Error in generate_response: {error_msg}")
        return error_msg

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_economic_summary() -> str:
    """
    Provides a general economic summary by calling relevant tools.
    This can be used for an initial dashboard view.
    """
    try:
        token_tool = TokenAnalysisTool()
        token_summary_raw = token_tool._run("general") # Get raw data from tool

        # Process the raw token summary to make it more engaging
        lines = token_summary_raw.split('\n')
        processed_summary = []
        for line in lines:
            if line.startswith('**'): # Token Name
                processed_summary.append(f"\n### {line.replace('**', '')}")
            elif 'Current Price:' in line:
                processed_summary.append(line.replace('• Current Price:', '  - **Current Price:**'))
            elif '24h Change:' in line:
                change_str = line.replace('• 24h Change:', '  - **24h Change:**')
                # Use regex to safely extract the percentage value
                match = re.search(r'(-?\d+\.\d+)%', line)
                change_value = float(match.group(1)) if match else 0.0

                if change_value < -10:
                    processed_summary.append(f"  - **Change:** 🔻 **Significant Drop!** {change_str.split(':')[1].strip()}")
                elif change_value < -5:
                    processed_summary.append(f"  - **Change:** 📉 **Moderate Dip.** {change_str.split(':')[1].strip()}")
                elif change_value > 0:
                    processed_summary.append(f"  - **Change:** 📈 **Up!** {change_str.split(':')[1].strip()}")
                else:
                    processed_summary.append(f"  - **Change:** ↔️ **Stable.** {change_str.split(':')[1].strip()}")
            elif 'Holder Count:' in line:
                processed_summary.append(line.replace('• Holder Count:', '  - **Holders:**'))
            elif 'Sub-Tokens:' in line:
                processed_summary.append(line.replace('• Sub-Tokens:', '  - **Sub-Tokens:**'))
        
        formatted_token_summary = "\n".join(processed_summary)
        
        summary = f"""
# 📊 Aurory Economic Overview

Welcome to your daily economic pulse check for the Aurory P2E game! Here's a snapshot of the current token market.

---

## Token Status: Market Watch

{formatted_token_summary}

---
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} (Istanbul Time)*
"""
        
        return summary
        
    except Exception as e:
        return f"Error retrieving economic summary: {str(e)}"

# Export agent for use in other modules
__all__ = ['agent_executor', 'generate_response', 'get_economic_summary', 'tools']
