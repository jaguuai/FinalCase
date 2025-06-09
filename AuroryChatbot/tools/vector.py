import streamlit as st
from llm import llm, embeddings
from graph import graph

from langchain_neo4j import Neo4jVector
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

try:
    # Create the Neo4jVector with error handling and updated syntax
    neo4jvector = Neo4jVector.from_existing_index(
        embeddings,
        graph=graph,
        index_name="aurory_docs",
        node_label="Document",
        text_node_property="content",
        embedding_node_property="embedding",
        retrieval_query="""
        RETURN
            node.content AS text,
            score,
            {
                source: node.source,
                docType: node.docType,
                title: node.title,
                economicSignificance: node.economicSignificance,
                influenceScore: node.influenceScore,
                socialImpact: node.socialImpact,
                eventType: node.eventType,
                socialImpact: node.socialImpact,
               

                tokens_mentioned:
                    [ (token:Token)<-[:DISCUSSES]-(node) | token.name ] +
                    [ (token:Token)<-[:REFERENCES]-(node) | token.name ] +
                    [ (token:Token)<-[:POTENTIAL_IMPACT]-(node) | token.name ],

                proposals_related:
                    [ (proposal:Proposal)<-[:DESCRIBES]-(node) | {
                        id: proposal.proposalId,
                        title: proposal.title
                    } ],

                nfts_related:
                    [ (nftitem:NftItem)<-[:ABOUT]-(node) | {
                        id: nftitem.id,
                        status: nftitem.status,
                        priceSOL: nftitem.priceSOL
                    } ],

                game_mechanics_related:
                    [ (gamemechanic:GameMechanic)<-[:MENTIONS]-(node) | {
                        description: gamemechanic.description,
                        name: gamemechanic.name
                    } ],

                source_url: CASE
                    WHEN node.docType = 'news' THEN 'https://aurorydocs.xyz/news/' + node.id
                    WHEN node.docType = 'tweet' THEN 'https://twitter.com/tweet/' + node.tweet_id
                    WHEN node.docType = 'dao_proposal' THEN 'https://gov.aurory.io/proposal/' + toString(node.proposalId)
                    ELSE node.source
                END
            } AS metadata
        """
    )

    # Create the retriever
    retriever = neo4jvector.as_retriever()

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


    document_qa_chain = create_stuff_documents_chain(llm, prompt)
    document_retriever = create_retrieval_chain(retriever, document_qa_chain)

except Exception as e:
    print(f"Error setting up vector search: {e}")
    document_retriever = None

def get_document(action_input):
    try:
        if isinstance(action_input, str):
            return document_retriever.invoke({"input": action_input})
        elif isinstance(action_input, dict):
            query = action_input.get("query", "")
            return document_retriever.invoke({"input": query})
        else:
            return {"error": "Invalid input format for document search."}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}