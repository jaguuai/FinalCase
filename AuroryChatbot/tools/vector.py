from llm import llm, embeddings
from graph import graph
from langchain_neo4j import Neo4jVector
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# Aurory Game Document Vector Setup
neo4jvector = Neo4jVector.from_existing_index(
    embeddings,                                    # (1)
    graph=graph,                                   # (2)
    index_name="aurory_docs",                      # (3) - Aurory documents index
    node_label="Document",                         # (4) - Document nodes
    text_node_property="content",                  # (5) - Document content property
    embedding_node_property="embedding",           # (6) - Embedding property
    retrieval_query="""
    RETURN node.content AS text, score, {
        source: node.source,
        doc_type: node.doc_type,
        title: node.title,
        timestamp: node.timestamp,
        author: node.author,
        tags: node.tags,
            (token:Token)<-[:DESCRIBES]-(node) | token.name
        ] + [
            (token:Token)<-[:REFERENCES]-(node) | token.name
        ] + [
            (token:Token)<-[:AFFECTS]-(node) | token.name
        ] + [
            (token:Token)<-[:POTENTIAL_IMPACT]-(node) | token.name
        ],
        nft_collection_mentioned: [
            (collection:Collection)-[:ABOUT]->(node) | collection.name
        ],
        proposal_related: [
            (proposal:Proposal)<-[:DESCRIBES]-(node) | {
                id: proposal.proposalId,
                title: proposal.title
            }
        ],
        economic_impact: node.economic_impact,
        risk_level: node.risk_level,
        source_url: CASE 
            WHEN node.doc_type = 'news' THEN node.source
            WHEN node.doc_type = 'tweet' THEN 'https://twitter.com/tweet/' + node.tweet_id
            WHEN node.doc_type = 'dao' THEN 'https://gov.aurory.io/proposal/' + toString(node.proposal_id)
            ELSE node.source
        END
    } AS metadata
    """
)

retriever = neo4jvector.as_retriever()

# Aurory-specific instructions
instructions = (
    "You are the Aurory Economy Strategy Assistant. Use the given context to provide economic insights about the Aurory game ecosystem. "
    "Focus on token economics, NFT markets, player strategies, and DAO governance. "
    "If the context doesn't contain relevant Aurory economic data, say you need more specific information. "
    "Always include risk assessments and strategic recommendations when applicable. "
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", instructions),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)

aurory_document_retriever = create_retrieval_chain(
    retriever,
    question_answer_chain
)

def get_aurory_insights(input):
    """
    Retrieve and analyze Aurory game documents for economic insights.
    
    Args:
        input (str): User query about Aurory economics
        
    Returns:
        dict: Response with economic insights and source documents
    """
    return aurory_document_retriever.invoke({"input": input})

# Alternative function names for different use cases
def search_aurory_documents(query):
    """Search through Aurory-related documents, news, tweets, and DAO proposals."""
    return get_aurory_insights(query)

def analyze_aurory_content(economic_query):
    """Analyze Aurory economic content based on stored documents."""
    return get_aurory_insights(economic_query)

# Advanced retrieval with filtering
def get_filtered_aurory_insights(input, doc_type=None, risk_level=None):
    """
    Get Aurory insights with additional filtering options.
    
    Args:
        input (str): User query
        doc_type (str): Filter by document type ('news', 'tweet', 'dao', etc.)
        risk_level (str): Filter by risk level ('high', 'medium', 'low')
    """
    # Create filtered retriever if filters are provided
    if doc_type or risk_level:
        filter_conditions = []
        if doc_type:
            filter_conditions.append(f"node.doc_type = '{doc_type}'")
        if risk_level:
            filter_conditions.append(f"node.risk_level = '{risk_level}'")
        
        filter_query = " AND ".join(filter_conditions)
        
        filtered_retrieval_query = f"""
        MATCH (node:Document)
        WHERE {filter_query}
        RETURN node.content AS text, score, {{
            source: node.source,
            doc_type: node.doc_type,
            title: node.title,
            risk_level: node.risk_level,
            economic_impact: node.economic_impact
        }} AS metadata
        """
        
        # Create new vector search with filter
        filtered_vector = Neo4jVector.from_existing_index(
            embeddings,
            graph=graph,
            index_name="aurory_docs",
            node_label="Document",
            text_node_property="content",
            embedding_node_property="embedding",
            retrieval_query=filtered_retrieval_query
        )
        
        filtered_retriever = filtered_vector.as_retriever()
        filtered_chain = create_retrieval_chain(filtered_retriever, question_answer_chain)
        
        return filtered_chain.invoke({"input": input})
    else:
        return get_aurory_insights(input)

# Usage examples:
"""
# Basic usage
response = get_aurory_insights("What are the current AURY token risks?")

# Search specific document types
dao_response = get_filtered_aurory_insights("governance proposals", doc_type="dao")

# Search by risk level
high_risk_response = get_filtered_aurory_insights("economic threats", risk_level="high")

# General document search
news_response = search_aurory_documents("latest Aurory market news")
"""