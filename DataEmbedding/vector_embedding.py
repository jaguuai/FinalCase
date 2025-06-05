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

# .env dosyasını yükle
load_dotenv("C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/neo4j.env")

    def __init__(self):
        """
        Vector embedding pipeline with OpenAI using .env variables
        """
        # Neo4j bilgilerini .env'den al
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Driver'ı ilişkiler için ayrı tut
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
        """Neo4j bağlantısını test et"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Bağlantı başarılı!' AS message")
                print("✅ Neo4j bağlantı testi:", result.single()["message"])
            return True
        except Exception as e:
            print(f"❌ Neo4j bağlantı hatası: {str(e)}")
            traceback.print_exc()
            return False

    def process_pdf_documents(self, pdf_folder_path: str) -> List[Document]:
        """PDF dosyalarını işle ve Document listesi döndür"""
        documents = []
        
        # Klasördeki tüm PDF dosyalarını işle
        for filename in os.listdir(pdf_folder_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_folder_path, filename)
                try:
                    proposal_id = None
                    # Updated regex to extract proposal ID from filenames like "DAOry Proposal #7.docx.pdf"
                    # It looks for a '#' followed by digits, or just digits after 'Proposal'
                    match = re.search(r'#(\d+)', filename) # Matches #7, #10
                    if match:
                        proposal_id = match.group(1) # Extracts '7' or '10'
                    elif 'Proposal' in filename: # Fallback if '#' is not present but 'Proposal' is
                        match = re.search(r'Proposal.*?(\d+)', filename, re.IGNORECASE)
                        if match:
                            proposal_id = match.group(1)
                    
                    loader = PyPDFLoader(file_path)
                    pdf_pages = loader.load()
                    
                    for page in pdf_pages:
                        # Sayfa içeriğini parçalara ayır
                        chunks = self.text_splitter.split_text(page.page_content)
                        
                        for i, chunk in enumerate(chunks):
                            # Metadata oluştur (proposal_id eklenmiş)
                            metadata = {
                                "source": filename,
                                "page": page.metadata["page"],
                                "doc_type": "dao_proposal",
                                "chunk_index": i,
                                "proposal_id": proposal_id  # Yeni alan
                            }
                            
                            # LangChain Document formatında ekle
                            documents.append(Document(
                                page_content=chunk,
                                metadata=metadata
                            ))
                except Exception as e:
                    print(f"PDF işleme hatası ({filename}): {str(e)}")
                    traceback.print_exc()
        
        print(f"✅ {len(documents)} PDF parçası işlendi")
        return documents

    def process_csv_data(self, csv_files: List[str]) -> List[Document]:
        """CSV dosyalarını işle ve Document listesi döndür"""
        documents = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Dosya adından türü belirle
                if 'news' in csv_file.lower():
                    docs = self._process_news_csv(df, csv_file)
                elif 'tweet' in csv_file.lower():
                    docs = self._process_tweet_csv(df, csv_file)
                else:
                    print(f"⚠️ Bilinmeyen CSV türü: {csv_file}")
                    continue
                    
                documents.extend(docs)
                
            except Exception as e:
                print(f"CSV işleme hatası ({csv_file}): {str(e)}")
                traceback.print_exc()
        
        print(f"✅ {len(documents)} CSV parçası işlendi")
        return documents

    def _process_news_csv(self, df: pd.DataFrame, source_file: str) -> List[Document]:
        """Haber CSV'sini işle"""
        documents = []
        
        for _, row in df.iterrows():
            try:
                # Haber içeriğini birleştir
                content = f"Başlık: {row.get('title', '')}\n\n{row.get('content', '')}"
                
                # Event türünü sınıflandır
                event_type = self.classify_event_type(content)
                economic_impact = self.assess_economic_impact(content, event_type)
                
                # Metadata oluştur
                metadata = {
                    "source": source_file,
                    "doc_type": "news",
                    "title": row.get('title', ''),
                    "url": row.get('url', ''),
                    "date": row.get('date', ''),
                    "event_type": event_type,
                    "economic_significance": economic_impact
                }
                
                # Document oluştur
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
                
            except Exception as e:
                print(f"Haber satırı işleme hatası: {str(e)}")
                continue
        
        return documents

    def _process_tweet_csv(self, df: pd.DataFrame, source_file: str) -> List[Document]:
        """Tweet CSV'sini işle"""
        documents = []
        
        for _, row in df.iterrows():
            try:
                content = row.get('text', '')
                
                # Tweet'i ekonomik açıdan analiz et
                economy_analysis = self.analyze_tweet_economy(content)
                impact_score = self.assess_tweet_impact(content, economy_analysis)
                
                # Metadata oluştur
                metadata = {
                    "source": source_file,
                    "doc_type": "tweet",
                    "tweet_id": row.get('id', ''),
                    "author": row.get('author', ''),
                    "date": row.get('date', ''),
                    "likes": row.get('likes', 0),
                    "retweets": row.get('retweets', 0),
                    "tokens": economy_analysis.get('tokens', []),
                    "nft_collections": economy_analysis.get('nft_collections', []),
                    "economic_significance": impact_score
                }
                
                # Document oluştur
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
                
            except Exception as e:
                print(f"Tweet satırı işleme hatası: {str(e)}")
                continue
        
        return documents

    def classify_event_type(self, content: str) -> str:
        """İçeriği analiz ederek event türünü belirle"""
        content_lower = content.lower()
        
        # Basit keyword tabanlı sınıflandırma
        if any(word in content_lower for word in ['partnership', 'collaboration', 'team up']):
            return 'partnership'
        elif any(word in content_lower for word in ['update', 'upgrade', 'new feature']):
            return 'product_update'
        elif any(word in content_lower for word in ['token', 'airdrop', 'staking']):
            return 'tokenomics'
        elif any(word in content_lower for word in ['nft', 'collection', 'mint']):
            return 'nft_launch'
        elif any(word in content_lower for word in ['tournament', 'competition', 'event']):
            return 'game_event'
        else:
            return 'general'

    def assess_economic_impact(self, content: str, event_type: str) -> int:
        """Ekonomik etkiyi 1-5 arası skorla"""
        content_lower = content.lower()
        score = 1
        
        # Event türüne göre base skor
        type_scores = {
            'partnership': 4,
            'tokenomics': 5,
            'nft_launch': 3,
            'product_update': 3,
            'game_event': 2,
            'general': 1
        }
        score = type_scores.get(event_type, 1)
        
        # Kritik kelimeler için bonus
        high_impact_words = ['major', 'significant', 'launch', 'million', 'billion', 'funding']
        for word in high_impact_words:
            if word in content_lower:
                score = min(5, score + 1)
                break
        
        return score

    def analyze_tweet_economy(self, tweet_text: str) -> Dict[str, Any]:
        """Tweet'in ekonomik içeriğini analiz et"""
        tweet_lower = tweet_text.lower()
        
        # Token isimleri (Aurory ekosistemine özgü)
        token_keywords = ['aury', 'aurory', 'token', 'coin']
        found_tokens = [token for token in token_keywords if token in tweet_lower]
        
        # NFT koleksiyonları
        nft_keywords = ['aurory', 'nefties', 'aurorian']
        found_collections = [nft for nft in nft_keywords if nft in tweet_lower]
        
        return {
            'tokens': found_tokens,
            'nft_collections': found_collections,
            'has_economic_content': len(found_tokens) > 0 or len(found_collections) > 0
        }

    def assess_tweet_impact(self, tweet_text: str, economy_analysis: Dict[str, Any]) -> int:
        """Tweet'in ekonomik etkisini değerlendir"""
        tweet_lower = tweet_text.lower()
        score = 1
        
        # Ekonomik içerik varsa base skor artır
        if economy_analysis.get('has_economic_content', False):
            score = 2
        
        # Yüksek etki kelimeleri
        high_impact_words = ['announcement', 'launch', 'partnership', 'update', 'new']
        for word in high_impact_words:
            if word in tweet_lower:
                score = min(5, score + 1)
        
        # Token/NFT sayısına göre bonus
        total_mentions = len(economy_analysis.get('tokens', [])) + len(economy_analysis.get('nft_collections', []))
        if total_mentions >= 2:
            score = min(5, score + 1)
        
        return score

    def clear_existing_documents(self):
        """Mevcut dokümanları temizle"""
        try:
            with self.driver.session() as session:
                # Önce vector index'i sil
                session.run("DROP INDEX aurory_docs IF EXISTS")
                # Document node'larını sil
                session.run("MATCH (d:Document) DETACH DELETE d")
                print("✅ Mevcut dokümanlar temizlendi")
        except Exception as e:
            print(f"⚠️ Temizleme sırasında hata (normal olabilir): {str(e)}")
            traceback.print_exc()

    def store_in_neo4j(self, documents: List[Document], index_name: str = "aurory_docs"):
        """Dokümanları Neo4j'ye kaydet"""
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
            print(f"✅ {len(documents)} doküman Neo4j'ye kaydedildi")
        except Exception as e:
            print(f"❌ Neo4j kaydetme hatası: {str(e)}")
            traceback.print_exc()

    def create_document_relationships(self):
        """Dokümanlar ile mevcut node'lar arasında ilişki kur (GÜNCELLENMİŞ)"""
        try:
            with self.driver.session() as session:
                print("🔍 Debug: Mevcut Document ve Proposal node'larını kontrol ediliyor...")
                
                # Document node'larını kontrol et ve proposal_id'leri topla
                doc_ids_check = session.run("""
                    MATCH (d:Document {doc_type: 'dao_proposal'})
                    WHERE d.proposal_id IS NOT NULL
                    RETURN d.proposal_id AS proposalId, d.source AS sourceFile
                """)
                found_doc_ids = []
                print("📄 Bulunan Document proposal_id'leri:")
                for record in doc_ids_check:
                    found_doc_ids.append(record["proposalId"])
                    print(f"  - Document proposal_id: {record['proposalId']} (from: {record['sourceFile']})")

                # Proposal node'larını kontrol et ve proposalId'leri topla
                prop_ids_check = session.run("""
                    MATCH (p:Proposal)
                    RETURN p.proposalId AS proposalId
                """)
                found_prop_ids = []
                print("🏛️ Bulunan Proposal proposalId'leri:")
                for record in prop_ids_check:
                    found_prop_ids.append(record["proposalId"])
                    print(f"  - Proposal proposalId: {record['proposalId']} (tip: {type(record['proposalId'])})")
                
                # Karşılaştırma için set'lere dönüştür
                set_doc_ids = set(map(str, found_doc_ids))
                set_prop_ids = set(map(str, found_prop_ids))

                # Ortak ID'leri kontrol et
                common_ids = set_doc_ids.intersection(set_prop_ids)
                if common_ids:
                    print(f"✅ Document ve Proposal arasında ortak ID'ler bulundu: {common_ids}")
                else:
                    print("❌ Document ve Proposal arasında ortak ID bulunamadı. Veri tutarlılığını kontrol edin.")
                
                # 1. Proposal'ları ilgili DAO önerilerine bağla (tip dönüşümü ile)
                result = session.run("""
                    MATCH (d:Document {doc_type: 'dao_proposal'})
                    WHERE d.proposal_id IS NOT NULL
                    MATCH (p:Proposal)
                    WHERE toString(p.proposalId) = toString(d.proposal_id)
                    MERGE (d)-[:DESCRIBES]->(p)
                    RETURN count(*) as linked_count
                """)
                
                linked_count = result.single()["linked_count"]
                print(f"✅ {linked_count} adet Document-Proposal bağlantısı kuruldu")
                
                # 2. Haberleri Token'lara bağla
                session.run("""
                    MATCH (d:Document {doc_type: 'news'})
                    MATCH (t:Token)
                    WHERE d.content CONTAINS t.name 
                    MERGE (d)-[:DISCUSSES]->(t)
                """)
                
                # 3. Ekonomik önemli haberleri Token'lara bağla
                session.run("""
                    MATCH (d:Document {doc_type: 'news'})
                    WHERE d.economic_significance >= 3
                    MATCH (t:Token)
                    MERGE (d)-[:AFFECTS]->(t)
                """)
                
                # 4. Tweet'lerde geçen token'ları bağla
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.tokens IS NOT NULL
                    UNWIND d.tokens AS tokenName
                    MATCH (t:Token {name: tokenName})
                    MERGE (d)-[:REFERENCES]->(t)
                """)
                
                # 5. Tweet'lerde geçen NFT koleksiyonlarını bağla
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.nft_collections IS NOT NULL
                    UNWIND d.nft_collections AS collectionName
                    MATCH (c:Collection {title: collectionName})
                    MERGE (d)-[:ABOUT]->(c)
                """)
                
                # 6. Ekonomik önemi yüksek tweet'leri token'lara bağla
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.economic_significance >= 3
                    MATCH (t:Token)
                    MERGE (d)-[:POTENTIAL_IMPACT]->(t)
                """)
                
                print("✅ Tüm ilişkiler başarıyla oluşturuldu")
        except Exception as e:
            print(f"❌ İlişki kurma hatası: {str(e)}")
            traceback.print_exc()

    def semantic_search(self, query_text: str, limit: int = 5) -> List[Document]:
        """Semantik arama yap ve sonuçları döndür"""
        try:
            vector_store = Neo4jVector.from_existing_index(
                embedding=self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name="aurory_docs",
                text_node_property="content"
            )
            
            # Benzerlik araması yap
            return vector_store.similarity_search(query_text, k=limit)
        except Exception as e:
            print(f"❌ Semantic search hatası: {str(e)}")
            traceback.print_exc()
            return []

    def close_connection(self):
        """Neo4j bağlantısını kapat"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j bağlantısı kapatıldı")

def main():
    # Pipeline'ı başlat (.env'den otomatik okuyacak)
    pipeline = VectorEmbeddingPipeline()
    
    try:
        # Bağlantı testi yap
        print("\n" + "="*50)
        print("Neo4j Bağlantı Testi...")
        print("="*50)
        if not pipeline.test_connection():
            print("❌ Neo4j bağlantısı başarısız. İşlemler durduruluyor.")
            return
        
        # PDF ve CSV dosya yolları
        pdf_folder = "C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/data_collection/DAOPDF"
        csv_files = [
            "C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/embedding_data/aurory_tweets.csv",
            "C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/embedding_data/aurory_news.csv"
        ]
        
        # 1. PDF dokümanları işle
        print("\n" + "="*50)
        print("PDF Dosyaları İşleniyor...")
        print("="*50)
        pdf_docs = pipeline.process_pdf_documents(pdf_folder)
        
        # 2. CSV verilerini işle
        print("\n" + "="*50)
        print("CSV Dosyaları İşleniyor...")
        print("="*50)
        csv_docs = pipeline.process_csv_data(csv_files)
        
        # 3. Tüm dokümanları birleştir
        all_documents = pdf_docs + csv_docs
        print(f"\nToplam {len(all_documents)} doküman hazır")
        
        # 3.5. Mevcut dokümanları temizle
        print("\n" + "="*50)
        print("Mevcut Dokümanlar Temizleniyor...")
        print("="*50)
        pipeline.clear_existing_documents()
        
        # 4. Neo4j'ye kaydet
        print("\n" + "="*50)
        print("Neo4j'ye Kaydediliyor...")
        print("="*50)
        pipeline.store_in_neo4j(all_documents)
        
        # 5. İlişkiler kur
        print("\n" + "="*50)
        print("Graf İlişkileri Kuruluyor...")
        print("="*50)
        pipeline.create_document_relationships()
        
        # 6. Test araması yap
        print("\n" + "="*50)
        print("Test Araması Yapılıyor...")
        print("="*50)
        results = pipeline.semantic_search("Token ekonomisi için önemli haberler neler?", limit=3)
        
        print("\nArama Sonuçları:")
        print("="*50)
        for i, doc in enumerate(results):
            source = doc.metadata.get('source', 'Bilinmiyor')
            title = doc.metadata.get('title', doc.metadata.get('tweet_id', 'Başlık Yok'))
            impact = doc.metadata.get('economic_significance', 0)
            content = doc.page_content[:250] + "..." if len(doc.page_content) > 250 else doc.page_content
            
            print(f"\n🔍 SONUÇ {i+1} - Etki: {'⭐' * impact}")
            print(f"📰 Başlık: {title}")
            print(f"📁 Kaynak: {source}")
            print("-"*50)
            print(content)
            print("-"*50)
    
    finally:
        # Bağlantıyı kapat
        pipeline.close_connection()

if __name__ == "__main__":
    main()