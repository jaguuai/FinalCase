import os
import re
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.schema import Document
from typing import List, Dict, Any
import traceback

load_dotenv("C:/Users/alice/OneDrive/Masaüstü/FinalCase/neo4j.env")

class VectorEmbeddingPipeline:
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password, openai_api_key]):
            raise ValueError("Neo4j or OpenAI environment variables are not set.")
        
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, 
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def test_connection(self) -> bool:
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful!' AS message")
                print("✅ Neo4j connection test:", result.single()["message"])
            return True
        except Exception as e:
            print(f"❌ Neo4j connection error: {str(e)}")
            traceback.print_exc()
            return False

    def process_pdf_documents(self, pdf_folder_path: str) -> List[Document]:
        documents = []
        
        if not os.path.exists(pdf_folder_path):
            print(f"❌ Error: PDF folder not found at '{pdf_folder_path}'")
            return []

        for filename in os.listdir(pdf_folder_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_folder_path, filename)
                try:
                    proposal_id = None
                    match = re.search(r'[#Pp]roposal\D*?(\d+)', filename, re.IGNORECASE)
                    if match:
                        proposal_id = match.group(1) 
                    
                    loader = PyPDFLoader(file_path)
                    pdf_pages = loader.load()
                    
                    for page in pdf_pages:
                        chunks = self.text_splitter.split_text(page.page_content)
                        
                        for i, chunk in enumerate(chunks):
                            metadata = {
                                "source": filename,
                                "page": page.metadata.get("page", 0),
                                "doc_type": "dao_proposal",
                                "chunk_index": i,
                                "proposal_id": proposal_id
                            }
                            documents.append(Document(
                                page_content=chunk,
                                metadata=metadata
                            ))
                except Exception as e:
                    print(f"Error processing PDF ({filename}): {str(e)}")
                    traceback.print_exc()
        
        print(f"✅ {len(documents)} PDF chunks processed")
        return documents

    def process_csv_data(self, csv_files: List[str]) -> List[Document]:
        documents = []
        
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                print(f"❌ Error: CSV file not found at '{csv_file}'")
                continue

            try:
                if not csv_file.lower().endswith('.csv'):
                    print(f"⚠️ Skipped: '{csv_file}' is not a CSV file.")
                    continue

                df = pd.read_csv(csv_file)
                
                if 'news' in csv_file.lower():
                    docs = self._process_news_csv(df, csv_file)
                elif 'tweet' in csv_file.lower():
                    docs = self._process_tweet_csv(df, csv_file)
                else:
                    print(f"⚠️ Unknown CSV type: {csv_file}")
                    continue
                    
                documents.extend(docs)
                
            except Exception as e:
                print(f"Error processing CSV ({csv_file}): {str(e)}")
                traceback.print_exc()
        
        print(f"✅ {len(documents)} CSV chunks processed")
        return documents

    def _process_news_csv(self, df: pd.DataFrame, source_file: str) -> List[Document]:
        documents = []
        
        if 'title' not in df.columns or 'content' not in df.columns:
            print(f"❌ Error: News CSV file '{source_file}' must contain 'title' and 'content' columns.")
            return []

        for _, row in df.iterrows():
            try:
                content = f"Title: {row.get('title', '')}\n\n{row.get('content', '')}"
                
                event_type = self.classify_event_type(content)
                economic_impact = self.assess_economic_impact(content, event_type)
                
                metadata = {
                    "source": source_file,
                    "doc_type": "news",
                    "title": row.get('title', ''),
                    "url": row.get('url', ''),
                    "date": str(row.get('date', '')),
                    "event_type": event_type,
                    "economic_significance": economic_impact
                }
                
                chunks = self.text_splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    documents.append(Document(
                        page_content=chunk,
                        metadata=chunk_metadata
                    ))
                
            except Exception as e:
                print(f"Error processing news row: {str(e)} for row: {row.to_dict()}")
                continue
        
        print(f"✅ {len(documents)} news documents processed from '{source_file}'")
        return documents

    def _process_tweet_csv(self, df: pd.DataFrame, source_file: str) -> List[Document]:
        documents = []
        
        if 'text' not in df.columns:
            print(f"❌ Error: Tweet CSV file '{source_file}' must contain a 'text' column.")
            return []

        for _, row in df.iterrows():
            try:
                content = str(row.get('text', ''))
                
                economy_analysis = self.analyze_tweet_economy(content)
                impact_score = self.assess_tweet_impact(content, economy_analysis)
                
                metadata = {
                    "source": source_file,
                    "doc_type": "tweet",
                    "tweet_id": str(row.get('id', '')),
                    "author": str(row.get('author', '')),
                    "date": str(row.get('date', '')),
                    "tokens": economy_analysis.get('tokens', []),
                    "nft_collections": economy_analysis.get('nft_collections', []),
                    "economic_significance": impact_score
                }
                
                chunks = self.text_splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    documents.append(Document(
                        page_content=chunk,
                        metadata=chunk_metadata
                    ))
                
            except Exception as e:
                print(f"Error processing tweet row: {str(e)} for row: {row.to_dict()}")
                continue
        
        print(f"✅ {len(documents)} tweet documents processed from '{source_file}'")
        return documents

    def classify_event_type(self, content: str) -> str:
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['partnership', 'collaboration', 'team up', 'join forces']):
            return 'partnership'
        elif any(word in content_lower for word in ['update', 'upgrade', 'new feature', 'patch', 'roadmap']):
            return 'product_update'
        elif any(word in content_lower for word in ['token', 'airdrop', 'staking', 'aury', 'xaury', 'nerite', 'ember', 'wisdom', 'economy']):
            return 'tokenomics'
        elif any(word in content_lower for word in ['nft', 'collection', 'mint', 'nefties', 'aurorian', 'aurorians', 'art']):
            return 'nft_launch'
        elif any(word in content_lower for word in ['tournament', 'competition', 'event', 'esports', 'challenge']):
            return 'game_event'
        elif any(word in content_lower for word in ['bug', 'exploit', 'security', 'hack']):
            return 'security_incident'
        elif any(word in content_lower for word in ['market', 'price', 'volume', 'trading', 'exchange', 'listing']):
            return 'market_activity'
        else:
            return 'general'

    def assess_economic_impact(self, content: str, event_type: str) -> int:
        content_lower = content.lower()
        score = 1
        
        type_scores = {
            'partnership': 4,
            'tokenomics': 5,
            'nft_launch': 3,
            'product_update': 3,
            'game_event': 2,
            'security_incident': 5,
            'market_activity': 4,
            'general': 1
        }
        score = type_scores.get(event_type, 1)
        
        high_impact_words = ['major', 'significant', 'launch', 'million', 'billion', 'funding', 'risk', 'threat', 'vulnerability', 'crash', 'boom']
        for word in high_impact_words:
            if word in content_lower:
                score = min(5, score + 1)
        
        if re.search(r'\d+\s*(million|billion|k|dollars|usd|sol|aury)', content_lower):
            score = min(5, score + 1)

        return score

    def analyze_tweet_economy(self, tweet_text: str) -> Dict[str, Any]:
        tweet_lower = tweet_text.lower()
        
        token_keywords = ['aury', 'aurory', 'token', 'coin', 'xaury', 'nerite', 'ember', 'wisdom', 'gems', 'essence']
        found_tokens = [token for token in token_keywords if token in tweet_lower]
        
        nft_keywords = ['nefties', 'aurorian', 'aurorians', 'nft', 'collection', 'floor price', 'marketplace']  
        found_collections = [nft for nft in nft_keywords if nft in tweet_lower]
        
        return {
            'tokens': list(set(found_tokens)),
            'nft_collections': list(set(found_collections)),
            'has_economic_content': len(found_tokens) > 0 or len(found_collections) > 0
        }

    def assess_tweet_impact(self, tweet_text: str, economy_analysis: Dict[str, Any]) -> int:
        tweet_lower = tweet_text.lower()
        score = 1
        
        if economy_analysis.get('has_economic_content', False):
            score = 2
        
        high_impact_words = ['announcement', 'launch', 'partnership', 'update', 'new', 'major', 'significant', 'price', 'market', 'volume', 'floor', 'risk', 'roadmap', 'beta']
        for word in high_impact_words:
            if word in tweet_lower:
                score = min(5, score + 1)
        
        total_mentions = len(economy_analysis.get('tokens', [])) + len(economy_analysis.get('nft_collections', []))
        if total_mentions >= 2:
            score = min(5, score + 1)
            
        if re.search(r'\d+[kM]|\bprice\b|\bvolume\b|\bmarketcap\b', tweet_lower):
            score = min(5, score + 1)
        
        return score

    def clear_existing_documents(self, doc_type: str = None):
        try:
            with self.driver.session() as session:
                print(f"Attempting to drop index 'aurory_docs' (if it exists)...")
                session.run("DROP INDEX aurory_docs IF EXISTS")
                print(f"✅ Index 'aurory_docs' dropped (if it existed).")

                if doc_type:
                    print(f"Deleting all Document nodes of type '{doc_type}' and their relationships...")
                    session.run(f"MATCH (d:Document {{doc_type: '{doc_type}'}}) DETACH DELETE d")
                    print(f"✅ Existing '{doc_type}' documents cleared.")
                else:
                    print(f"Deleting ALL Document nodes and their relationships...")
                    session.run("MATCH (d:Document) DETACH DELETE d")
                    print(f"✅ ALL existing documents cleared.")
        except Exception as e:
            print(f"⚠️ Error during cleanup (might be normal if index or nodes don't exist): {str(e)}")
            traceback.print_exc()

    def store_in_neo4j(self, documents: List[Document], index_name: str = "aurory_docs"):
        if not documents:
            print("ℹ️ No documents to store in Neo4j.")
            return

        try:
            Neo4jVector.from_documents(
                documents=documents,
                embedding=self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name=index_name,
                node_label="Document",
                text_node_property="content",
                embedding_node_property="embedding"
            )
            print(f"✅ {len(documents)} documents saved to Neo4j")
        except Exception as e:
            print(f"❌ Neo4j save error: {str(e)}")
            traceback.print_exc()

    def create_document_relationships(self):
        try:
            with self.driver.session() as session:
                print("\n--- Creating Relationships ---")

                result = session.run("""
                    MATCH (d:Document {doc_type: 'dao_proposal'})
                    WHERE d.proposal_id IS NOT NULL
                    MATCH (p:Proposal)
                    WITH d, p, apoc.text.regexGroups(toString(p.proposalId), '.*(\\d+).*') AS p_id_match_raw
                    WHERE size(p_id_match_raw) > 0
                    WITH d, p, p_id_match_raw[0][1] AS p_normalized_id
                    WHERE toString(p_normalized_id) = toString(d.proposal_id)
                    MERGE (d)-[:DESCRIBES]->(p)
                    RETURN count(*) as linked_count
                """)
                linked_count_dao = result.single()["linked_count"]
                print(f"✅ {linked_count_dao} Document-Proposal relationships created (:DESCRIBES)")
                
                session.run("""
                    MATCH (d:Document {doc_type: 'news'})
                    MATCH (t:Token)
                    WHERE toLower(d.content) CONTAINS toLower(t.name)
                    MERGE (d)-[:DISCUSSES]->(t)
                """)
                print("✅ News-Token relationships created (:DISCUSSES)")
                
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.tokens IS NOT NULL
                    UNWIND d.tokens AS tokenName
                    MATCH (t:Token {name: toLower(tokenName)})
                    MERGE (d)-[:REFERENCES]->(t)
                """)
                print("✅ Tweet-Token relationships created (:REFERENCES)")
                
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.nft_collections IS NOT NULL
                    UNWIND d.nft_collections AS collectionKeyword
                    MATCH (ni:NftItem)
                    WHERE toLower(ni.name) CONTAINS toLower(collectionKeyword) OR toLower(ni.collection) CONTAINS toLower(collectionKeyword)
                    MERGE (d)-[:REFERENCES]->(ni)
                """)
                print("✅ Tweet-NftItem relationships created (:REFERENCES)")
                
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.economic_significance >= 2
                    MATCH (t:Token)
                    WHERE toLower(d.content) CONTAINS toLower(t.name)
                    MERGE (d)-[:POTENTIAL_IMPACT]->(t)
                """)
                print("✅ Tweet-Token relationships created (:POTENTIAL_IMPACT) [Economic Significance >= 2]")
                
                game_mechanics = session.run("MATCH (gm:GameMechanic) RETURN gm.description AS description").data()
                game_mechanic_descriptions = [gm['description'].lower() for gm in game_mechanics if gm['description']]

                if game_mechanic_descriptions:
                    query_news_game_mechanic = f"""
                    MATCH (d:Document)
                    WHERE d.doc_type = 'news'
                    UNWIND $game_mechanic_descriptions AS gmDesc
                    MATCH (gm:GameMechanic)
                    WHERE toLower(gm.description) = gmDesc AND toLower(d.content) CONTAINS gmDesc
                    MERGE (d)-[:DISCUSSES_MECHANIC]->(gm)
                    """
                    session.run(query_news_game_mechanic, game_mechanic_descriptions=game_mechanic_descriptions)
                    print(f"✅ News-GameMechanic relationships created (:DISCUSSES_MECHANIC) for {len(game_mechanic_descriptions)} mechanics.")
                else:
                    print("⚠️ No GameMechanics found in Neo4j, News-GameMechanic relationships not created.")

                print("✅ All relationships successfully created")
        except Exception as e:
            print(f"❌ Relationship creation error: {str(e)}")
            traceback.print_exc()

    def semantic_search(self, query_text: str, limit: int = 5, filters: Dict[str, Any] = None, score_threshold: float = 0.65) -> List[Document]:
        try:
            base_retrieval_query = """
            RETURN node.content AS text, score, {
                source: node.source,
                page: node.page,
                doc_type: node.doc_type,
                chunk_index: node.chunk_index,
                proposal_id: node.proposal_id,
                title: node.title,
                url: node.url,
                date: node.date,
                event_type: node.event_type,
                economic_significance: node.economic_significance,
                tweet_id: node.tweet_id,
                author: node.author,
                tokens: node.tokens, 
                nft_collections: node.nft_collections
            } AS metadata
            """

            where_clauses = []
            if filters:
                if "doc_type" in filters and filters["doc_type"] is not None:
                    where_clauses.append(f"node.doc_type = '{filters['doc_type']}'")
                if "economic_significance_min" in filters and filters["economic_significance_min"] is not None:
                    where_clauses.append(f"node.economic_significance >= {filters['economic_significance_min']}")
                if "proposal_id" in filters and filters["proposal_id"] is not None:
                    where_clauses.append(f"toString(node.proposal_id) = '{filters['proposal_id']}'")
                if "author" in filters and filters["author"] is not None:
                    where_clauses.append(f"toLower(node.author) CONTAINS toLower('{filters['author']}')")
                if "tokens_mentioned" in filters and filters["tokens_mentioned"] is not None:
                    token_list_str = ", ".join([f"'{token.lower()}'" for token in filters['tokens_mentioned']])
                    where_clauses.append(f"ANY(t IN node.tokens WHERE toLower(t) IN [{token_list_str}])")
                if "nft_collections_mentioned" in filters and filters["nft_collections_mentioned"] is not None:
                    collection_list_str = ", ".join([f"'{col.lower()}'" for col in filters['nft_collections_mentioned']])
                    where_clauses.append(f"ANY(c IN node.nft_collections WHERE toLower(c) IN [{collection_list_str}])")
            
            final_retrieval_query = "MATCH (node:Document)"
            if where_clauses:
                final_retrieval_query += " WHERE " + " AND ".join(where_clauses)
            final_retrieval_query += base_retrieval_query

            vector_store = Neo4jVector.from_existing_index(
                embedding=self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name="aurory_docs",
                text_node_property="content",
                embedding_node_property="embedding",
                retrieval_query=final_retrieval_query
            )

            docs_and_scores = vector_store.similarity_search_with_score(query_text, k=limit*2)

            filtered_results = [
                doc for doc, score in docs_and_scores if score >= score_threshold
            ]
            
            return filtered_results[:limit]
        except Exception as e:
            print(f"❌ Semantic search error: {str(e)}")
            traceback.print_exc()
            return []
def print_search_results(title: str, results: List[Document]):
    print(f"\n--- {title} ---")
    if results:
        for i, doc in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Content: {doc.page_content[:200]}...")  # Print first 200 chars
            for key, value in doc.metadata.items():
                print(f"  {key.capitalize()}: {value}")
            print("-" * 30)
    else:
        print("No results found.")

if __name__ == "__main__":
    pipeline = VectorEmbeddingPipeline()

    if not pipeline.test_connection():
        print("Exiting due to Neo4j connection failure.")
        exit()

    # Clear existing documents before processing new ones (optional, but good for clean runs)
    pipeline.clear_existing_documents()

    # Define paths to your CSV and PDF files
    # Make sure these paths are correct for your environment
    csv_files = [
        "C:/Users/alice/OneDrive/Masaüstü/FinalCase/DataEmbedding/DataGathering/embedding_data/aurory_tweets.csv",
        "C:/Users/alice/OneDrive/Masaüstü/FinalCase/DataEmbedding/DataGathering/embedding_data/aurory_news.csv"
    ]
    pdf_folder_path = "C:/Users/alice/OneDrive/Masaüstü/FinalCase/DataEmbedding/DataGathering/embedding_data/DAOPDF"

    # Process documents
    all_documents = []
    all_documents.extend(pipeline.process_csv_data(csv_files))
    all_documents.extend(pipeline.process_pdf_documents(pdf_folder_path))

    # Store processed documents in Neo4j
    if all_documents:
        pipeline.store_in_neo4j(all_documents)
        pipeline.create_document_relationships()
    else:
        print("No documents were processed. Skipping Neo4j storage and relationship creation.")

    # Example Semantic Searches
    print("\n--- Performing Semantic Searches ---")

    # Search for news about 'AURY' token
    print_search_results(
        "News about AURY token with high economic significance",
        pipeline.semantic_search(
            "What is the latest news on AURY token?", 
            filters={"doc_type": "news", "economic_significance_min": 3}, 
            limit=5
        )
    )

    # Search for tweets discussing 'Nefties' NFT collection
    print_search_results(
        "Tweets discussing Nefties NFT collection",
        pipeline.semantic_search(
            "What are people saying about Nefties NFTs?", 
            filters={"doc_type": "tweet", "nft_collections_mentioned": ["nefties"]}, 
            limit=5
        )
    )

    # Search for DAO proposals related to game mechanics
    print_search_results(
        "DAO proposals related to game mechanics",
        pipeline.semantic_search(
            "Show me DAO proposals about game mechanics or new features.", 
            filters={"doc_type": "dao_proposal"}, 
            limit=5
        )
    )