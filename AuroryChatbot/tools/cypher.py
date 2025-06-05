from llm import llm
from graph import graph
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from typing import Dict, Any


# Enhanced Aurory Cypher Generation Templates
AURORY_CYPHER_GENERATION_TEMPLATE = """
You are an Aurory Play-to-Earn (P2E) game economy expert converting user questions into Neo4j Cypher queries.
You analyze Aurory's blockchain game ecosystem, including token economics, NFT marketplace, player activities, DAO governance, and social media sentiment.

Convert user questions based on the provided schema.
Only use node types, relationship types, and properties defined in the schema.
Do not use relationship types or properties not present in the schema.
Do not return entire nodes or embedding properties.

**Special Rules:**
- Token names: AURY (main governance token)
- Game Token names: XAURY (staked AURY), NERITE, EMBER, WISDOM
- NFT collections: Nefties, Aurorians
- Blockchain: Solana (prices in SOL)
- Date format: Use datetime()
- Wallet addresses: 44-character base58 strings
- Price values: Float (USD and SOL)
- Default LIMIT: 20 (unless specified otherwise)
- Case insensitive (use CONTAINS or toLower())
- Social sentiment: POSITIVE, NEGATIVE, NEUTRAL
- Engagement metrics: likes, retweets, replies, mentions

**Schema:**
{schema}

**Example Queries:**
1. Token price with document sentiment analysis:
   MATCH (t:Token)<-[:DISCUSSES]-(d:Document {doc_type: 'tweet'})
   WHERE t.name = 'aurory' 
   RETURN t.usd, t.percentChange24h, 
          avg(d.economic_significance) as avg_social_impact,
          count(d) as mention_count
   
2. NFT performance with social buzz from documents:
   MATCH (c:Collection)<-[:ABOUT]-(d:Document {doc_type: 'tweet'})
   RETURN c.name, 
          sum(d.likes + d.retweets) as social_engagement,
          count(d) as buzz_count
   
3. DAO proposals with community response from documents:
   MATCH (p:Proposal)<-[:DESCRIBES]-(d:Document)
   WHERE p.status = 'ACTIVE'
   RETURN p.title, 
          count(d) as document_coverage,
          avg(d.economic_significance) as community_interest

Question: {question}

Cypher Query:
"""

MARKET_SENTIMENT_TEMPLATE = """
You are an Aurory market sentiment expert analyzing NFT performance, token prices, and social media buzz.

Collections: Nefties (game characters), Aurorians (avatar NFTs)
Sentiment Analysis: Combine on-chain metrics with social media sentiment
Risk Assessment: Market performance vs community sentiment alignment

Schema:
{schema}

Special Rules:
- Social engagement proxy: Use Document likes, retweets, economic_significance
- Twitter metrics from Document nodes: likes, retweets, author engagement
- Performance categories: Calculate from price changes and document sentiment
- Community response strength: HIGH (>10 related documents), MODERATE (5-10), LOW (<5)
- Buzz analysis: Use Document relationships and engagement metrics

Question: {question}
Cypher:
"""

DAO_COMMUNITY_TEMPLATE = """
You are an Aurory DAO governance expert analyzing active proposals and community social media response.

Proposal Types: Economic, Governance, Technical, Community
Community Response: Twitter engagement, Discord activity, voting participation
Impact Assessment: Proposal impact vs community sentiment correlation

Schema:
{schema}

Special Rules:
- Active proposals: status = 'ACTIVE'
- Community response strength from Documents: 
  * HIGH: >10 related documents AND avg(economic_significance) > 3
  * MODERATE: 5-10 related documents AND avg(economic_significance) 2-3
  * LOW: <5 related documents OR avg(economic_significance) < 2
- Engagement metrics: Sum of likes + retweets from related tweet documents
- Document coverage analysis: Count documents describing each proposal
- Community sentiment proxy: economic_significance and engagement levels

Question: {question}
Cypher:
"""

TOKEN_ECONOMICS_SENTIMENT_TEMPLATE = """
You are an Aurory token economics expert analyzing AURY token performance with social media sentiment.

Token Analysis: Price movements, supply dynamics, staking metrics
Sentiment Correlation: Social media buzz vs price performance
Risk Assessment: Market sentiment vs tokenomics health

Schema:
{schema}

Special Rules:
- Price-sentiment correlation using Documents:
  * BULLISH_ALIGNED: price_change_24h > 0 AND avg(economic_significance) > 3
  * BEARISH_ALIGNED: price_change_24h < 0 AND avg(economic_significance) < 2  
  * DIVERGENT: price vs document sentiment mismatch (RISK indicator)
- Social metrics from Documents: tweet count, total likes+retweets, author diversity
- Document analysis: economic_significance as sentiment proxy
- Market sentiment strength: document_count + avg(engagement_metrics)

Question: {question}
Cypher:
"""

PLAYER_STRATEGY_TEMPLATE = """
You are an Aurory player economy expert analyzing successful earning strategies from social media and on-chain data.

Strategy Analysis: Player earnings, token accumulation, NFT trading
Social Intelligence: Twitter strategy discussions, Discord tips, Reddit guides
Performance Correlation: Social strategy mentions vs actual player performance

Schema:
{schema}

Special Rules:
- Successful players: earnings/amount > 1000 AND userLevel > 50
- Strategy analysis from Documents: Look for strategy-related tweets and news
- Document-based strategy mentions: economic_significance > 3 AND content contains strategy keywords
- Popular strategies derived from Document analysis: 
  * STAKING: Documents mentioning staking + high economic_significance
  * NFT_TRADING: Documents about Collections + high engagement
  * GAMEPLAY: Documents about tournaments, quests + player mentions
- Performance correlation: Cross-reference wallet performance with document mentions

Question: {question}
Cypher:
"""

ECOSYSTEM_RISK_TEMPLATE = """
You are an Aurory ecosystem risk expert analyzing economic risks from blockchain data and community discussions.

Risk Categories: Economic, Governance, Market, Technical, Community
Data Sources: On-chain metrics, social media sentiment, community feedback
Risk Assessment: Multi-dimensional risk analysis with community sentiment

Schema:
{schema}

Special Rules:
- Economic risks calculated from existing data:
  * HIGH: percentChange24h < -10% OR floorPriceSOL drop > 50%
  * MODERATE: percentChange24h between -5% to -10% OR low document coverage
  * LOW: stable metrics AND positive document sentiment (economic_significance > 3)
- Community risk indicators from Documents:
  * SENTIMENT_RISK: avg(economic_significance) < 2 for documents in last 30 days
  * ENGAGEMENT_RISK: total document count down > 50% compared to previous period
  * GOVERNANCE_RISK: low proposal document coverage (< 3 documents per proposal)
- Risk correlation: token performance vs document sentiment alignment
- Document-based risk assessment: economic_significance trends and engagement patterns

Question: {question}
Cypher:
"""

# Enhanced template selector function
def get_aurory_cypher_template(analysis_type: str = "general") -> str:
    templates = {
        "general": AURORY_CYPHER_GENERATION_TEMPLATE,
        "market_sentiment": MARKET_SENTIMENT_TEMPLATE,
        "dao_community": DAO_COMMUNITY_TEMPLATE,
        "token_sentiment": TOKEN_ECONOMICS_SENTIMENT_TEMPLATE,
        "player_strategy": PLAYER_STRATEGY_TEMPLATE,
        "ecosystem_risk": ECOSYSTEM_RISK_TEMPLATE
    }
    return templates.get(analysis_type, AURORY_CYPHER_GENERATION_TEMPLATE)

# Enhanced Dynamic Cypher Chain
class EnhancedAuroryCypherChain(GraphCypherQAChain):
    def _determine_template(self, question: str) -> str:
        """Determine the template based on question content with enhanced keyword matching for specific use cases."""
        question_lower = question.lower()
        
        # Refined Multi-keyword pattern matching for specific use cases
        # Use Case 1: "How are Nefties and Aurorians performing in the market, and what's the Twitter buzz around these collections?"
        market_sentiment_patterns = [
            ['nefties', 'aurorians', 'market', 'performing', 'twitter', 'buzz'],
            ['nft', 'collection', 'market', 'sentiment', 'social media']
        ]
        
        # Use Case 2: "What are the active DAO proposals and how is the community responding to them on social media?"
        dao_community_patterns = [
            ['dao', 'proposals', 'active', 'community', 'responding', 'social media'],
            ['governance', 'proposals', 'community', 'response']
        ]
        
        # Use Case 3: "What's the current market sentiment for AURY tokens based on recent Twitter discussions and price movements?"
        token_sentiment_patterns = [
            ['aury', 'market', 'sentiment', 'twitter', 'discussions', 'price', 'movements'],
            ['token', 'sentiment', 'price', 'social media']
        ]
        
        # Use Case 4: "What earning strategies are successful players discussing on Twitter, and what does the current token economics suggest?"
        player_strategy_patterns = [
            ['earning', 'strategies', 'successful', 'players', 'twitter', 'token', 'economics'],
            ['player', 'strategy', 'social media', 'economy']
        ]
        
        # Use Case 5: "What are the main economic risks for Aurory ecosystem based on recent data and community discussions?"
        ecosystem_risk_patterns = [
            ['economic', 'risks', 'aurory', 'ecosystem', 'recent', 'data', 'community', 'discussions'],
            ['risk', 'analysis', 'ecosystem', 'vulnerabilities']
        ]
        
        # Check for pattern matches. A higher match percentage ensures more accurate template selection.
        if self._matches_patterns(question_lower, market_sentiment_patterns, match_percentage=0.6):
            return "market_sentiment"
        elif self._matches_patterns(question_lower, dao_community_patterns, match_percentage=0.6):
            return "dao_community"
        elif self._matches_patterns(question_lower, token_sentiment_patterns, match_percentage=0.6):
            return "token_sentiment"
        elif self._matches_patterns(question_lower, player_strategy_patterns, match_percentage=0.6):
            return "player_strategy"
        elif self._matches_patterns(question_lower, ecosystem_risk_patterns, match_percentage=0.6):
            return "ecosystem_risk"
        else:
            return "general"
    
    def _matches_patterns(self, question: str, patterns: list, match_percentage: float = 0.6) -> bool:
        """
        Check if question matches any of the keyword patterns based on a given match percentage.
        A higher match_percentage means more keywords from the pattern must be present.
        """
        for pattern in patterns:
            matches = sum(1 for keyword in pattern if keyword in question)
            if matches >= len(pattern) * match_percentage:
                return True
        return False

    def _call(self, inputs: Dict[str, Any], run_manager=None):
        """Custom call with enhanced template selection"""
        question = inputs['query']
        
        # Select appropriate template
        analysis_type = self._determine_template(question)
        template_str = get_aurory_cypher_template(analysis_type)
        
        # Schema based on your existing data structure
        schema = """
        Nodes: 
        - Token(name, usd, percentChange24h, marketCapUsd, circulatingSupply)
        - GameToken(symbol,craft_cost,description,success_rate,daily_earn_limit,game)
        - Wallet(address, amount, userLevel)
        - NFTItem(id, priceSOL, timestamp)
        - Collection(name,timestamp)
        - Transaction(signature, fee, slot, timestamp)
        - Proposal(proposalId, title)
        - GameMechanic(level_multiplier,base_cost,skill_points_per_level,description)
        - Document(content, doc_type, source, economic_significance, proposal_id, tokens, nft_collections, likes, retweets, author, date)
        - Council(name,description,electionCycle)
        - CouncilMember(name, twitter, role)
        
        Relationships: 
        - (Wallet)-[:HOLDS]->(GameToken)
        - (CouncilMember)-[:MEMBER_OF]->(Council)
        - (CouncilMember)-[:OWNS]->(Wallet)
        - (NFTItem)-[:BELONGS_TO]->(Collection)
        - (Wallet)-[:SENT]->(Transaction)
        - (Token)-[:HAS_SUBTOKEN]->(GameToken)
        - (Token)-[:GENERATES]->(GameToken)
        - (Token)-[:ENABLES]->(GameToken)
        - (Document)-[:DESCRIBES]->(Proposal)
        - (Document)-[:DISCUSSES]->(Token)
        - (Document)-[:AFFECTS]->(Token)
        - (Document)-[:REFERENCES]->(Token)
        - (Document)<-[:ABOUT]-(Collection)
        - (Document)-[:POTENTIAL_IMPACT]->(Token)
        """
        
        # Create prompt with selected template
        prompt = PromptTemplate.from_template(template_str)
        self.cypher_generation_chain.prompt = prompt
        
        # Add schema to inputs
        inputs['schema'] = schema
        
        return super()._call(inputs, run_manager=run_manager)

# Initialize enhanced cypher chain
enhanced_cypher_qa = EnhancedAuroryCypherChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True
)

# Convenience function for question analysis
def analyze_aurory_question(question: str) -> Dict[str, Any]:
    """Analyze question and return relevant information"""
    chain = EnhancedAuroryCypherChain.from_llm(llm, graph=graph, verbose=True, allow_dangerous_requests=True)
    template_type = chain._determine_template(question)
    
    return {
        "question": question,
        "template_type": template_type,
        "analysis_focus": _get_analysis_focus(template_type),
        "expected_data": _get_expected_data_types(template_type)
    }

def _get_analysis_focus(template_type: str) -> str:
    focus_map = {
        "market_sentiment": "NFT market performance + social media sentiment correlation",
        "dao_community": "DAO governance + community social media response analysis", 
        "token_sentiment": "Token economics + social media sentiment alignment",
        "player_strategy": "Player earning strategies + social media strategy discussions",
        "ecosystem_risk": "Multi-dimensional risk assessment + community sentiment",
        "general": "General Aurory ecosystem analysis"
    }
    return focus_map.get(template_type, "General analysis")

def _get_expected_data_types(template_type: str) -> list:
    data_map = {
        "market_sentiment": ["NFT prices", "social sentiment", "Twitter mentions", "collection performance"],
        "dao_community": ["active proposals", "voting data", "community response", "social engagement"],
        "token_sentiment": ["token prices", "social sentiment", "price-sentiment correlation", "market metrics"],
        "player_strategy": ["player earnings", "strategy mentions", "social discussions", "performance data"],
        "ecosystem_risk": ["risk metrics", "sentiment analysis", "community feedback", "market indicators"],
        "general": ["various Aurory ecosystem data"]
    }
    return data_map.get(template_type, ["general ecosystem data"])

# Sample query examples for your existing data structure
def get_sample_queries() -> Dict[str, str]:
    """Sample Cypher queries that work with your existing data"""
    return {
        "nft_market_buzz": """
        // NFT collections performance with Twitter buzz
        MATCH (c:Collection)<-[:ABOUT]-(d:Document {doc_type: 'tweet'})
        RETURN c.name as collection,
               c.floorPriceSOL as floor_price,
               count(d) as tweet_mentions,
               sum(d.likes + d.retweets) as total_engagement,
               avg(d.economic_significance) as avg_sentiment_score,
               collect(DISTINCT d.author)[0..5] as top_authors
        ORDER BY total_engagement DESC
        LIMIT 10
        """,
        
        "dao_proposals_community": """
        // Active DAO proposals with community response
        MATCH (p:Proposal)<-[:DESCRIBES]-(d:Document)
        WHERE p.status = 'ACTIVE' OR p.votingDeadline > datetime()
        RETURN p.title as proposal,
               p.votingDeadline as deadline,
               count(d) as document_coverage,
               avg(d.economic_significance) as community_interest,
               sum(CASE WHEN d.doc_type = 'tweet' THEN d.likes + d.retweets ELSE 0 END) as social_engagement
        ORDER BY community_interest DESC, social_engagement DESC
        """,
        
        "token_market_sentiment": """
        // AURY token sentiment from Twitter discussions
        MATCH (t:Token)<-[:DISCUSSES|REFERENCES]-(d:Document {doc_type: 'tweet'})
        WHERE t.name CONTAINS 'AURY' OR t.name CONTAINS 'Aurory'
        RETURN t.name as token,
               t.usd as current_price,
               t.percentChange24h as price_change,
               count(d) as tweet_mentions,
               avg(d.economic_significance) as sentiment_score,
               sum(d.likes + d.retweets) as engagement,
               CASE 
                 WHEN t.percentChange24h > 0 AND avg(d.economic_significance) > 3 THEN 'BULLISH_ALIGNED'
                 WHEN t.percentChange24h < 0 AND avg(d.economic_significance) < 2 THEN 'BEARISH_ALIGNED'
                 ELSE 'DIVERGENT'
               END as sentiment_alignment
        """,
        
        "player_earning_strategies": """
        // Player strategies from social media and performance
        MATCH (w:Wallet)
        WHERE w.amount > 1000 AND w.userLevel > 50
        OPTIONAL MATCH (w)<-[:REFERENCES]-(d:Document {doc_type: 'tweet'})
        WHERE d.content CONTAINS 'strategy' OR d.content CONTAINS 'earning'
        RETURN w.userLevel as player_level,
               w.amount as holdings,
               count(d) as strategy_mentions,
               avg(d.economic_significance) as strategy_sentiment,
               collect(DISTINCT d.author)[0..3] as mentioned_by
        ORDER BY w.amount DESC
        LIMIT 20
        """,
        
        "ecosystem_risk_analysis": """
        // Multi-dimensional risk analysis
        MATCH (t:Token)
        OPTIONAL MATCH (t)<-[:DISCUSSES|AFFECTS]-(d:Document)
        WHERE d.date > date() - duration('P30D') // Last 30 days
        WITH t, 
             count(d) as doc_count,
             avg(d.economic_significance) as sentiment_avg,
             t.percentChange24h as price_change
        RETURN t.name as asset,
               price_change,
               doc_count,
               sentiment_avg,
               CASE 
                 WHEN price_change < -10 OR sentiment_avg < 2 THEN 'HIGH_RISK'
                 WHEN price_change < -5 OR sentiment_avg < 3 THEN 'MODERATE_RISK'
                 ELSE 'LOW_RISK'
               END as risk_level,
               CASE 
                 WHEN doc_count < 5 THEN 'LOW_COVERAGE'
                 WHEN doc_count < 15 THEN 'MODERATE_COVERAGE'
                 ELSE 'HIGH_COVERAGE'
               END as community_coverage
        ORDER BY 
          CASE 
            WHEN risk_level = 'HIGH_RISK' THEN 1
            WHEN risk_level = 'MODERATE_RISK' THEN 2
            ELSE 3
          END,
          sentiment_avg ASC
        """
    }

__all__ = ['enhanced_cypher_qa', 'analyze_aurory_question', 'get_sample_queries']
