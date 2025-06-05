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
# Bu yolun projenizdeki .env dosyasının gerçek konumunu gösterdiğinden emin olun.
load_dotenv("C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/neo4j.env")

class VectorEmbeddingPipeline:
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
        # Bu sürücü, manuel Cypher sorgularını çalıştırmak ve ilişkiler oluşturmak için kullanılır.
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, 
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Metinleri vektör temsillerine dönüştürmek için embedding modelini başlat
        # NOT: LangChain 0.0.9'dan sonra OpenAIEmbeddings sınıfı 'langchain-openai' paketine taşınmıştır.
        # Bu paketi 'pip install -U langchain-openai' ile kurmanız ve
        # 'from langchain_openai import OpenAIEmbeddings' olarak import etmeniz önerilir.
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key
        )
        
        # Büyük metinleri yönetilebilir parçalara bölmek için metin bölücüyü yapılandır
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,     # Her metin parçasının maksimum boyutu
            chunk_overlap=200,   # Parçalar arasındaki çakışma miktarı (bağlamı korumak için)
            length_function=len, # Uzunluk hesaplama fonksiyonu (karakter sayısı)
        )

    def test_connection(self) -> bool:
        """Neo4j bağlantısını test eder."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Bağlantı başarılı!' AS message")
                print("✅ Neo4j bağlantı testi:", result.single()["message"])
            return True
        except Exception as e:
            print(f"❌ Neo4j bağlantı hatası: {str(e)}")
            traceback.print_exc() # Hata izini yazdır (hata ayıklama için faydalı)
            return False

    def process_pdf_documents(self, pdf_folder_path: str) -> List[Document]:
        """
        Belirtilen klasördeki PDF dosyalarını işler ve LangChain Document nesneleri listesi döndürür.
        DAO önerileri için proposal_id'yi dosya adından çıkarmaya çalışır.
        """
        documents = []
        
        for filename in os.listdir(pdf_folder_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_folder_path, filename)
                try:
                    proposal_id = None
                    # Dosya adından proposal_id çıkarmak için regex kullanılır.
                    # Örnek: "DAOry Proposal #7.docx.pdf" -> "7"
                    match = re.search(r'#(\d+)', filename) 
                    if match:
                        proposal_id = match.group(1) 
                    elif 'Proposal' in filename: 
                        match = re.search(r'Proposal.*?(\d+)', filename, re.IGNORECASE)
                        if match:
                            proposal_id = match.group(1)
                    
                    loader = PyPDFLoader(file_path)
                    pdf_pages = loader.load() # PDF'i sayfalara yükler
                    
                    for page in pdf_pages:
                        # Her sayfa içeriğini parçalara ayırır
                        chunks = self.text_splitter.split_text(page.page_content)
                        
                        for i, chunk in enumerate(chunks):
                            # Her parça için meta verileri oluşturur
                            metadata = {
                                "source": filename,
                                "page": page.metadata["page"],
                                "doc_type": "dao_proposal", # Belge türü olarak DAO önerisi
                                "chunk_index": i,
                                "proposal_id": proposal_id  # Çıkarılan proposal_id
                            }
                            
                            # LangChain Document formatında belgeyi ekler
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
        """
        Belirtilen CSV dosyalarını işler ve LangChain Document nesneleri listesi döndürür.
        Dosya adına göre (haber veya tweet) özel işleme yöntemlerini çağırır.
        """
        documents = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                if 'news' in csv_file.lower():
                    docs = self._process_news_csv(df, csv_file)
                elif 'tweet' in csv_file.lower():
                    docs = self._process_tweet_csv(df, csv_file)
                else:
                    print(f"⚠️ Bilinmeyen CSV türü: {csv_file}")
                    continue
                    
                documents.extend(docs) # İşlenen belgeleri ana listeye ekle
                
            except Exception as e:
                print(f"CSV işleme hatası ({csv_file}): {str(e)}")
                traceback.print_exc()
        
        print(f"✅ {len(documents)} CSV parçası işlendi")
        return documents

    def _process_news_csv(self, df: pd.DataFrame, source_file: str) -> List[Document]:
        """Haber CSV verilerini işler ve Document nesneleri döndürür."""
        documents = []
        
        for _, row in df.iterrows():
            try:
                # Haber başlığı ve içeriğini birleştirir
                content = f"Başlık: {row.get('title', '')}\n\n{row.get('content', '')}"
                
                # İçeriği analiz ederek olay türünü ve ekonomik etkiyi belirler
                event_type = self.classify_event_type(content)
                economic_impact = self.assess_economic_impact(content, event_type)
                
                # Meta verileri oluşturur
                metadata = {
                    "source": source_file,
                    "doc_type": "news",
                    "title": row.get('title', ''),
                    "url": row.get('url', ''),
                    "date": row.get('date', ''),
                    "event_type": event_type,
                    "economic_significance": economic_impact # Ekonomik önem puanı
                }
                
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
                
            except Exception as e:
                print(f"Haber satırı işleme hatası: {str(e)}")
                continue
        
        return documents

    def _process_tweet_csv(self, df: pd.DataFrame, source_file: str) -> List[Document]:
        """Tweet CSV verilerini işler ve Document nesneleri döndürür."""
        documents = []
        
        for _, row in df.iterrows():
            try:
                content = row.get('text', '')
                
                # Tweet'i ekonomik açıdan analiz eder (token ve NFT koleksiyonları)
                economy_analysis = self.analyze_tweet_economy(content)
                # Tweet'in ekonomik etkisini değerlendirir
                impact_score = self.assess_tweet_impact(content, economy_analysis)
                
                # Meta verileri oluşturur
                metadata = {
                    "source": source_file,
                    "doc_type": "tweet",
                    "tweet_id": row.get('id', ''),
                    "author": row.get('author', ''),
                    "date": row.get('date', ''),
                    "likes": row.get('likes', 0),
                    "retweets": row.get('retweets', 0),
                    "tokens": economy_analysis.get('tokens', []), # Bahsedilen tokenlar
                    "nft_collections": economy_analysis.get('nft_collections', []), # Bahsedilen NFT koleksiyonları
                    "economic_significance": impact_score # Ekonomik önem puanı
                }
                
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
                
            except Exception as e:
                print(f"Tweet satırı işleme hatası: {str(e)}")
                continue
        
        return documents

    def classify_event_type(self, content: str) -> str:
        """İçeriği analiz ederek olayın türünü belirler."""
        content_lower = content.lower()
        
        # Anahtar kelimelere dayalı basit sınıflandırma
        if any(word in content_lower for word in ['partnership', 'collaboration', 'team up']):
            return 'partnership'
        elif any(word in content_lower for word in ['update', 'upgrade', 'new feature']):
            return 'product_update'
        elif any(word in content_lower for word in ['token', 'airdrop', 'staking', 'aury', 'xaury', 'nerite', 'ember', 'wisdom']):
            return 'tokenomics'
        elif any(word in content_lower for word in ['nft', 'collection', 'mint', 'nefties', 'aurorian', 'aurorians']):
            return 'nft_launch'
        elif any(word in content_lower for word in ['tournament', 'competition', 'event']):
            return 'game_event'
        else:
            return 'general'

    def assess_economic_impact(self, content: str, event_type: str) -> int:
        """Bir içeriğin ekonomik etkisini 1-5 arası bir skorla değerlendirir."""
        content_lower = content.lower()
        score = 1
        
        # Olay türüne göre temel skor atar
        type_scores = {
            'partnership': 4,
            'tokenomics': 5,
            'nft_launch': 3,
            'product_update': 3,
            'game_event': 2,
            'general': 1
        }
        score = type_scores.get(event_type, 1)
        
        # Yüksek etki belirten kelimeler için bonus puan ekler
        high_impact_words = ['major', 'significant', 'launch', 'million', 'billion', 'funding', 'risk', 'threat', 'vulnerability']
        for word in high_impact_words:
            if word in content_lower:
                score = min(5, score + 1) # Skoru 5'i geçmeyecek şekilde artır
                # break # İlk eşleşmede dur (isteğe bağlı, daha fazla kelime kontrolü için kaldırılabilir)
        
        return score

    def analyze_tweet_economy(self, tweet_text: str) -> Dict[str, Any]:
        """
        Bir tweet'in ekonomik içeriğini (bahsedilen tokenlar ve NFT koleksiyonları) analiz eder.
        NOT: Kullanılan embedding model tweet'lerdeki "Nefties", "Aurorians" gibi
        domain'e özel jargon/kısaltmaları tam olarak tanımayabilir.
        Bu fonksiyon, bu terimleri anahtar kelimelerle manuel olarak tespit ederek
        arama filtrelerinin daha etkili olmasını sağlamaya yardımcı olur.
        Daha iyi anlama için modele fine-tuning yapılması (bu kodun kapsamı dışında)
        veya daha gelişmiş bir embedding modeli kullanılması düşünülebilir.
        """
        tweet_lower = tweet_text.lower()
        
        # Aurory ekosistemine özgü token isimleri
        token_keywords = ['aury', 'aurory', 'token', 'coin', 'xaury', 'nerite', 'ember', 'wisdom']
        found_tokens = [token for token in token_keywords if token in tweet_lower]
        
        # Aurory NFT koleksiyonları
        nft_keywords = ['nefties', 'aurorian', 'aurorians'] 
        found_collections = [nft for nft in nft_keywords if nft in tweet_lower]
        
        return {
            'tokens': list(set(found_tokens)), # Tekrar edenleri kaldır
            'nft_collections': list(set(found_collections)), # Tekrar edenleri kaldır
            'has_economic_content': len(found_tokens) > 0 or len(found_collections) > 0
        }

    def assess_tweet_impact(self, tweet_text: str, economy_analysis: Dict[str, Any]) -> int:
        """Bir tweet'in ekonomik etkisini değerlendirir."""
        tweet_lower = tweet_text.lower()
        score = 1
        
        # Ekonomik içerik varsa temel skoru artır
        if economy_analysis.get('has_economic_content', False):
            score = 2
        
        # Yüksek etki kelimeleri için bonus puan
        high_impact_words = ['announcement', 'launch', 'partnership', 'update', 'new', 'major', 'significant', 'price', 'market', 'volume', 'floor', 'risk']
        for word in high_impact_words:
            if word in tweet_lower:
                score = min(5, score + 1)
        
        # Bahsedilen token/NFT sayısına göre bonus
        total_mentions = len(economy_analysis.get('tokens', [])) + len(economy_analysis.get('nft_collections', []))
        if total_mentions >= 2:
            score = min(5, score + 1)
        
        return score

    def clear_existing_documents(self):
        """Mevcut 'Document' düğümlerini ve 'aurory_docs' vektör indeksini Neo4j'den temizler."""
        try:
            with self.driver.session() as session:
                # Önce var olan vektör indeksini siler
                session.run("DROP INDEX aurory_docs IF EXISTS")
                # Tüm Document düğümlerini ve bunlara bağlı tüm ilişkileri siler
                session.run("MATCH (d:Document) DETACH DELETE d")
                print("✅ Mevcut dokümanlar temizlendi")
        except Exception as e:
            print(f"⚠️ Temizleme sırasında hata (normal olabilir, eğer indeks veya düğüm yoksa): {str(e)}")
            traceback.print_exc()

    def store_in_neo4j(self, documents: List[Document], index_name: str = "aurory_docs"):
        """LangChain Document nesnelerini Neo4j'ye kaydeder ve vektör indeksine ekler."""
        try:
            # Neo4jVector.from_documents, indeks yoksa otomatik olarak oluşturur
            Neo4jVector.from_documents(
                documents=documents,
                embedding=self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name=index_name,              # Vektör indeksinin adı
                node_label="Document",              # Düğümlerin etiketi
                text_node_property="content",       # Metin içeriği özelliği
                embedding_node_property="embedding" # Gömülü vektör özelliği
            )
            print(f"✅ {len(documents)} doküman Neo4j'ye kaydedildi")
        except Exception as e:
            print(f"❌ Neo4j kaydetme hatası: {str(e)}")
            traceback.print_exc()

    def create_document_relationships(self):
        """
        İşlenen dokümanlar ile mevcut Neo4j düğümleri (Proposal, Token, Collection) arasında
        ilişkiler kurar.
        """
        try:
            with self.driver.session() as session:
                print("🔍 Debug: Mevcut Document ve Proposal node'larını kontrol ediliyor...")
                
                # DAO önerisi dokümanlarından proposal_id'leri ve kaynak dosyaları kontrol et
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

                # Mevcut Proposal düğümlerinin proposalId'lerini kontrol et
                prop_ids_check = session.run("""
                    MATCH (p:Proposal)
                    RETURN p.proposalId AS proposalId
                """)
                found_prop_ids = []
                print("🏛️ Bulunan Proposal proposalId'leri:")
                for record in prop_ids_check:
                    found_prop_ids.append(record["proposalId"])
                    # Tip dönüşümü hata ayıklama için:
                    print(f"  - Proposal proposalId: {record['proposalId']} (tip: {type(record['proposalId'])})")
                
                # Ortak ID'leri bulup veri tutarlılığını kontrol et
                set_doc_ids = set(map(str, found_doc_ids))
                set_prop_ids = set(map(str, found_prop_ids))

                common_ids = set_doc_ids.intersection(set_prop_ids)
                if common_ids:
                    print(f"✅ Document ve Proposal arasında ortak ID'ler bulundu: {common_ids}")
                else:
                    print("❌ Document ve Proposal arasında ortak ID bulunamadı. Veri tutarlılığını kontrol edin. Bu, DAO önerileri için ilişkilerin kurulmamasına neden olabilir.")
                
                # 1. DAO önerisi dokümanlarını ilgili Proposal düğümlerine bağlar.
                # toString() kullanarak tip tutarsızlıklarını önler.
                result = session.run("""
                    MATCH (d:Document {doc_type: 'dao_proposal'})
                    WHERE d.proposal_id IS NOT NULL
                    MATCH (p:Proposal)
                    WHERE toString(p.proposalId) = toString(d.proposal_id)
                    MERGE (d)-[:DESCRIBES]->(p)
                    RETURN count(*) as linked_count
                """)
                linked_count = result.single()["linked_count"]
                print(f"✅ {linked_count} adet Document-Proposal bağlantısı kuruldu (:DESCRIBES)")
                
                # 2. Haber dokümanlarını, içeriğinde adı geçen Token düğümlerine bağlar.
                # toLower() kullanarak büyük/küçük harf duyarlılığını kaldırır.
                session.run("""
                    MATCH (d:Document {doc_type: 'news'})
                    MATCH (t:Token)
                    WHERE toLower(d.content) CONTAINS toLower(t.name) 
                    MERGE (d)-[:DISCUSSES]->(t)
                """)
                print("✅ News-Token bağlantıları kuruldu (:DISCUSSES)")
                
                # 3. Ekonomik önemi yüksek haber dokümanlarını ilgili Token düğümlerine bağlar.
                session.run("""
                    MATCH (d:Document {doc_type: 'news'})
                    WHERE d.economic_significance >= 3
                    MATCH (t:Token)
                    WHERE toLower(d.content) CONTAINS toLower(t.name)
                    MERGE (d)-[:AFFECTS]->(t)
                """)
                print("✅ News-Token bağlantıları kuruldu (:AFFECTS) [Ekonomik Önem > 3]")
                
                # 4. Tweet dokümanlarını, meta verilerinde bahsedilen Token düğümlerine bağlar.
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.tokens IS NOT NULL
                    UNWIND d.tokens AS tokenName
                    MATCH (t:Token {name: toLower(tokenName)})
                    MERGE (d)-[:REFERENCES]->(t)
                """)
                print("✅ Tweet-Token bağlantıları kuruldu (:REFERENCES)")
                
                # 5. Tweet dokümanlarını, meta verilerinde bahsedilen NFT Collection düğümlerine bağlar.
                # Cypher sorgusu içindeki yorum kaldırıldı.
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.nft_collections IS NOT NULL
                    UNWIND d.nft_collections AS collectionName
                    MATCH (c:Collection {name: collectionName}) 
                    MERGE (d)-[:ABOUT]->(c)
                """)
                print("✅ Tweet-Collection bağlantıları kuruldu (:ABOUT)")
                
                # 6. Ekonomik önemi yüksek tweet dokümanlarını ilgili Token düğümlerine bağlar.
                session.run("""
                    MATCH (d:Document {doc_type: 'tweet'})
                    WHERE d.economic_significance >= 3
                    MATCH (t:Token)
                    WHERE toLower(d.content) CONTAINS toLower(t.name)
                    MERGE (d)-[:POTENTIAL_IMPACT]->(t)
                """)
                print("✅ Tweet-Token bağlantıları kuruldu (:POTENTIAL_IMPACT) [Ekonomik Önem > 3]")
                
                print("✅ Tüm ilişkiler başarıyla oluşturuldu")
        except Exception as e:
            print(f"❌ İlişki kurma hatası: {str(e)}")
            traceback.print_exc()

    def semantic_search(self, query_text: str, limit: int = 5, filters: Dict[str, Any] = None, score_threshold: float = 0.65) -> List[Document]:
        """
        Belirtilen sorgu metnine göre anlamsal arama yapar ve isteğe bağlı filtreler uygular.
        score_threshold: Döndürülecek dokümanların sahip olması gereken minimum benzerlik puanı.
        """
        try:
            # Temel retrieval sorgusu: Tüm Document özelliklerini metadata olarak döndürür
            # Cypher'da RETURN içinde # yorumları kullanılamaz, kaldırıldı.
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
                likes: node.likes,
                retweets: node.retweets,
                tokens: node.tokens, 
                nft_collections: node.nft_collections
            } AS metadata
            """

            where_clauses = []
            if filters:
                # Belge türüne göre filtreleme
                if "doc_type" in filters and filters["doc_type"] is not None:
                    where_clauses.append(f"node.doc_type = '{filters['doc_type']}'")
                # Minimum ekonomik önem puanına göre filtreleme
                if "economic_significance_min" in filters and filters["economic_significance_min"] is not None:
                    where_clauses.append(f"node.economic_significance >= {filters['economic_significance_min']}")
                # Proposal ID'ye göre filtreleme (DAO önerileri için)
                if "proposal_id" in filters and filters["proposal_id"] is not None:
                    where_clauses.append(f"toString(node.proposal_id) = '{filters['proposal_id']}'")
                # Yazar adına göre filtreleme (tweetler için)
                if "author" in filters and filters["author"] is not None:
                    where_clauses.append(f"toLower(node.author) CONTAINS toLower('{filters['author']}')")
                # Bahsedilen tokenlara göre filtreleme
                if "tokens_mentioned" in filters and filters["tokens_mentioned"] is not None:
                    # `tokens` özelliği bir string listesi olduğu varsayımıyla
                    token_list_str = ", ".join([f"'{token.lower()}'" for token in filters['tokens_mentioned']])
                    where_clauses.append(f"ANY(t IN node.tokens WHERE toLower(t) IN [{token_list_str}])")
                # Bahsedilen NFT koleksiyonlarına göre filtreleme
                if "nft_collections_mentioned" in filters and filters["nft_collections_mentioned"] is not None:
                    collection_list_str = ", ".join([f"'{col.lower()}'" for col in filters['nft_collections_mentioned']])
                    where_clauses.append(f"ANY(c IN node.nft_collections WHERE toLower(c) IN [{collection_list_str}])")
            
            # Dinamik Cypher sorgusunu oluştur
            final_retrieval_query = "MATCH (node:Document)"
            if where_clauses:
                final_retrieval_query += " WHERE " + " AND ".join(where_clauses)
            final_retrieval_query += base_retrieval_query

            # Filtrelenmiş arama için yeni Neo4jVector nesnesi oluştur
            # Benzerlik araması için daha fazla aday almak adına k limitini iki katına çıkarıyoruz,
            # böylece eşik sonrası filtreleme için yeterli veri olur.
            vector_store = Neo4jVector.from_existing_index(
                embedding=self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name="aurory_docs",
                text_node_property="content",
                embedding_node_property="embedding", # Embedding özelliği burada da belirtilmeli
                retrieval_query=final_retrieval_query # Dinamik sorguyu buraya iletiyoruz
            )

            # Benzerlik araması yapar ve sonuçları döndürür. Score da dahil olmak üzere.
            # Daha sonra score_threshold ile filtrelenecek.
            docs_and_scores = vector_store.similarity_search_with_score(query_text, k=limit*2) # Limit*2 ile daha fazla aday al

            # Eşiğe göre filtreleme
            filtered_results = [
                doc for doc, score in docs_and_scores if score >= score_threshold
            ]
            
            # İstenen limit kadar sonuç döndür
            return filtered_results[:limit]
        except Exception as e:
            print(f"❌ Semantic search hatası: {str(e)}")
            traceback.print_exc()
            return []

    def get_nft_market_buzz(self, nft_collections: List[str], limit: int = 5) -> Dict[str, List[Document]]:
        """
        "How are Nefties and Aurorians performing in the market, and what's the Twitter buzz around these collections?"
        Bu kullanım durumu için NFT koleksiyonlarının piyasa performansını ve Twitter tartışmalarını getirir.
        """
        results = {}
        for collection_name in nft_collections:
            print(f"\n--- '{collection_name}' için Arama Başlatılıyor ---")
            # NFT koleksiyonu ile ilgili tweet'leri arar
            tweet_query = f"Latest discussions, sentiment, and market buzz around {collection_name} on Twitter."
            # Filtreye koleksiyon adının küçük harf karşılığını ekleriz
            tweet_filters = {"doc_type": "tweet", "nft_collections_mentioned": [collection_name.lower()]}
            # Varsayılan score_threshold (0.65) burada kullanılacak. İsterseniz değiştirebilirsiniz.
            tweets = self.semantic_search(tweet_query, limit=limit, filters=tweet_filters)
            results[f"{collection_name}_tweets"] = tweets
            print(f"✅ {len(tweets)} adet '{collection_name}' ile ilgili tweet bulundu.")

            # NFT koleksiyonu ile ilgili ekonomik haberleri arar
            news_query = f"Market performance, floor price trends, and news about {collection_name}."
            # Ekonomik önemi olan haberleri filtreleriz
            news_filters = {"doc_type": "news", "economic_significance_min": 2} 
            # Varsayılan score_threshold (0.65) burada kullanılacak. İsterseniz değiştirebilirsiniz.
            news = self.semantic_search(news_query, limit=limit, filters=news_filters)
            results[f"{collection_name}_news"] = news
            print(f"✅ {len(news)} adet '{collection_name}' ile ilgili haber/ekonomik veri bulundu.")
        return results

    def get_dao_community_response(self, query: str = "active DAO proposals and community response", limit: int = 5) -> Dict[str, List[Document]]:
        """
        "What are the active DAO proposals and how is the community responding to them on social media?"
        Bu kullanım durumu için aktif DAO önerilerini ve topluluk tepkilerini getirir.
        """
        results = {}
        print(f"\n--- '{query}' için Arama Başlatılıyor ---")
        
        # DAO önerileri için arama yapar
        dao_filters = {"doc_type": "dao_proposal"}
        # 'active' durumunu doğrudan Document'ın meta verisinde tutmadığımız için, arama metni ile hedefleriz
        dao_proposals = self.semantic_search("What are the current active DAO proposals?", limit=limit, filters=dao_filters)
        results["dao_proposals"] = dao_proposals
        print(f"✅ {len(dao_proposals)} adet DAO önerisi bulundu.")

        # Topluluk tepkileri için tweet'leri arar
        # DAO önerileriyle ilgili tweet'lerin `proposal_id`'si tweet meta verisinde yok,
        # bu yüzden genel DAO tartışmalarını ararız veya daha sonra manuel olarak ilişkilendirebiliriz.
        community_tweet_query = f"Community sentiment, discussions, and response regarding DAO proposals."
        community_tweets = self.semantic_search(community_tweet_query, limit=limit, filters={"doc_type": "tweet", "economic_significance_min": 1})
        results["community_tweets"] = community_tweets
        print(f"✅ {len(community_tweets)} adet topluluk tepkisi tweet'i bulundu.")
        return results

    def get_token_market_sentiment(self, token_name: str, limit: int = 5) -> Dict[str, List[Document]]:
        """
        "What's the current market sentiment for AURY tokens based on recent Twitter discussions and price movements?"
        Bu kullanım durumu için belirli bir token için piyasa duyarlılığını ve Twitter tartışmalarını getirir.
        """
        results = {}
        print(f"\n--- '{token_name}' için Piyasa Duyarlılığı ve Twitter Tartışması Arama Başlatılıyor ---")
        
        # Token ile ilgili tweet'leri arar
        tweet_query = f"Market sentiment, discussions, and price buzz about {token_name} token on Twitter."
        # token_name'i küçük harfe çevirerek filtrelere ekleriz
        tweet_filters = {"doc_type": "tweet", "tokens_mentioned": [token_name.lower()], "economic_significance_min": 2}
        tweets = self.semantic_search(tweet_query, limit=limit, filters=tweet_filters)
        results["token_tweets"] = tweets
        print(f"✅ {len(tweets)} adet '{token_name}' ile ilgili tweet bulundu.")

        # Token ile ilgili haberleri (fiyat hareketleri için) arar
        news_query = f"Price movements, market trends, and economic news about {token_name} token."
        news_filters = {"doc_type": "news", "economic_significance_min": 3, "tokens_mentioned": [token_name.lower()]}
        news = self.semantic_search(news_query, limit=limit, filters=news_filters)
        results["token_news"] = news
        print(f"✅ {len(news)} adet '{token_name}' ile ilgili haber bulundu.")
        return results

    def get_player_earning_strategies(self, query: str = "successful player earning strategies", limit: int = 5) -> Dict[str, List[Document]]:
        """
        "What earning strategies are successful players discussing on Twitter, and what does the current token economics suggest?"
        Bu kullanım durumu için başarılı oyuncu kazanç stratejilerini ve token ekonomisi ilişkisini getirir.
        """
        results = {}
        print(f"\n--- '{query}' için Arama Başlatılıyor ---")
        
        # Oyuncu stratejileri ile ilgili tweet'leri arar
        tweet_filters = {"doc_type": "tweet"}
        player_tweets = self.semantic_search("Player earning strategies, tips, gameplay tactics, and discussions in Aurory.", limit=limit, filters=tweet_filters)
        results["player_strategy_tweets"] = player_tweets
        print(f"✅ {len(player_tweets)} adet oyuncu stratejisi tweet'i bulundu.")

        # Token ekonomisi ile ilgili genel dokümanları (haberler) arar
        economy_news_filters = {"doc_type": "news", "economic_significance_min": 3}
        economy_news = self.semantic_search("Aurory token economics, staking mechanisms, rewards, inflation, and deflation.", limit=limit, filters=economy_news_filters)
        results["token_economy_news"] = economy_news
        print(f"✅ {len(economy_news)} adet token ekonomisi haberi bulundu.")
        return results

    def get_ecosystem_economic_risks(self, query: str = "main economic risks for Aurory ecosystem", limit: int = 5) -> Dict[str, List[Document]]:
        """
        "What are the main economic risks for Aurory ecosystem based on recent data and community discussions?"
        Bu kullanım durumu için Aurory ekosistemi için ana ekonomik riskleri getirir.
        """
        results = {}
        print(f"\n--- '{query}' için Arama Başlatılıyor ---")
        
        # Ekonomik riskleri belirten haberleri arar (yüksek ekonomik önemde olanlar)
        news_filters = {"doc_type": "news", "economic_significance_min": 4} # Risks usually have higher significance
        risk_news = self.semantic_search("Potential economic threats, vulnerabilities, market risks, and financial concerns in Aurory.", limit=limit, filters=news_filters)
        results["risk_news"] = risk_news
        print(f"✅ {len(risk_news)} adet ekonomik risk haberi bulundu.")

        # Topluluk tartışmalarında geçen riskleri arar (tweetler)
        tweet_filters = {"doc_type": "tweet", "economic_significance_min": 3}
        risk_tweets = self.semantic_search("Community concerns, potential issues, and economic risks discussions on social media.", limit=limit, filters=tweet_filters)
        results["risk_tweets"] = risk_tweets
        print(f"✅ {len(risk_tweets)} adet risk odaklı tweet bulundu.")
        return results


    def close_connection(self):
        """Neo4j bağlantısını kapatır."""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j bağlantısı kapatıldı")

def print_search_results(title: str, results: List[Document]):
    """Arama sonuçlarını başlık ve detaylarla düzenli bir şekilde konsola yazdırır."""
    print(f"\n--- {title} ---")
    if not results:
        print("Sonuç bulunamadı.")
        return
    for i, doc in enumerate(results):
        source = doc.metadata.get('source', 'Bilinmiyor')
        doc_type = doc.metadata.get('doc_type', 'Bilinmiyor')
        # Daha bilgilendirici bir başlık veya ID seçimi
        content_id = doc.metadata.get('title', doc.metadata.get('tweet_id', doc.metadata.get('proposal_id', 'Başlık Yok')))
        impact = doc.metadata.get('economic_significance', 0)
        # İçeriği kısalt ve sonunda '...' ekle
        content = doc.page_content[:250] + "..." if len(doc.page_content) > 250 else doc.page_content
        
        print(f"\n🔍 SONUÇ {i+1} - Tür: {doc_type.upper()} - Etki: {'⭐' * impact}")
        print(f"📰 ID/Başlık: {content_id}")
        print(f"📁 Kaynak: {source}")
        print("-" * 50)
        print(content)
        print("-" * 50)

def main():
    """
    Ana fonksiyon, pipeline'ı başlatır, verileri işler, Neo4j'ye kaydeder,
    ilişkileri kurar ve tanımlanan kullanım senaryoları için test aramaları yapar.
    """
    pipeline = VectorEmbeddingPipeline()
    
    try:
        # Neo4j bağlantısını test et
        print("\n" + "="*50)
        print("Neo4j Bağlantı Testi...")
        print("="*50)
        if not pipeline.test_connection():
            print("❌ Neo4j bağlantısı başarısız. İşlemler durduruluyor.")
            return
            
        # PDF ve CSV dosyalarının yollarını tanımlayın.
        # Bu yolların kendi sisteminizdeki gerçek yollarla eşleştiğinden emin olun.
        pdf_folder = "C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/data_collection/DAOPDF"
        csv_files = [
            "C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/embedding_data/aurory_tweets.csv",
            "C:/Users/alice/OneDrive/Masaüstü/P2E-Economy-Assistant-AuroryGame/embedding_data/aurory_news.csv"
        ]
        
        # 1. PDF dokümanlarını işle (DAO önerileri)
        print("\n" + "="*50)
        print("PDF Dosyaları İşleniyor...")
        print("="*50)
        pdf_docs = pipeline.process_pdf_documents(pdf_folder)
        
        # 2. CSV verilerini işle (haberler ve tweetler)
        print("\n" + "="*50)
        print("CSV Dosyaları İşleniyor...")
        print("="*50)
        csv_docs = pipeline.process_csv_data(csv_files)
        
        # 3. Tüm işlenmiş dokümanları birleştir
        all_documents = pdf_docs + csv_docs
        print(f"\nToplam {len(all_documents)} doküman hazır")
        
        # 3.5. Mevcut dokümanları ve indeksi temizle (her çalıştırmada temiz bir başlangıç için)
        print("\n" + "="*50)
        print("Mevcut Dokümanlar Temizleniyor...")
        print("="*50)
        pipeline.clear_existing_documents()
        
        # 4. İşlenen dokümanları Neo4j'ye kaydet ve embedding'lerini oluştur
        print("\n" + "="*50)
        print("Neo4j'ye Kaydediliyor...")
        print("="*50)
        pipeline.store_in_neo4j(all_documents)
        
        # 5. Dokümanlar ve diğer varlıklar arasında ilişkileri kur (Token, Collection, Proposal)
        print("\n" + "="*50)
        print("Graf İlişkileri Kuruluyor...")
        print("="*50)
        pipeline.create_document_relationships()
        
        # 6. Tanımlanan kullanım senaryoları için test aramaları yap
        print("\n" + "="*50)
        print("Kullanım Örnekleri İçin Test Aramaları Başlatılıyor...")
        print("="*50)

        # Use Case 1: Nefties ve Aurorians piyasa performansı ve Twitter buzz
        print("\n>>> KULLANIM SENARYOSU 1: Nefties ve Aurorians'ın piyasa performansı ve Twitter'daki yankısı <<<")
        # score_threshold'u örnek olarak 0.60'a düşürerek daha fazla eşleşme yakalamayı deneyelim
        nft_buzz_results = pipeline.get_nft_market_buzz(["Nefties", "Aurorians"], limit=2)
        print_search_results("Nefties Twitter Buzz (Örnek Tweetler)", nft_buzz_results.get("Nefties_tweets", []))
        print_search_results("Nefties Market News (Örnek Haberler)", nft_buzz_results.get("Nefties_news", []))
        print_search_results("Aurorians Twitter Buzz (Örnek Tweetler)", nft_buzz_results.get("Aurorians_tweets", []))
        print_search_results("Aurorians Market News (Örnek Haberler)", nft_buzz_results.get("Aurorians_news", []))
        
        # Use Case 2: Aktif DAO önerileri ve topluluk tepkisi
        print("\n>>> KULLANIM SENARYOSU 2: Aktif DAO önerileri ve topluluğun sosyal medyadaki tepkisi <<<")
        dao_community_results = pipeline.get_dao_community_response(limit=3)
        print_search_results("Aktif DAO Önerileri (PDF Dokümanları)", dao_community_results["dao_proposals"])
        print_search_results("DAO Topluluk Tepkileri (Genel Tweet Tartışmaları)", dao_community_results["community_tweets"])

        # Use Case 3: AURY token piyasa duyarlılığı ve fiyat hareketleri
        print("\n>>> KULLANIM SENARYOSU 3: AURY tokenleri için mevcut piyasa duyarlılığı ve fiyat hareketleri <<<")
        # score_threshold'u örnek olarak 0.55'e düşürerek daha fazla eşleşme yakalamayı deneyelim
        aury_sentiment_results = pipeline.get_token_market_sentiment("AURY", limit=3)
        print_search_results("AURY Token Twitter Duyarlılığı", aury_sentiment_results["token_tweets"])
        print_search_results("AURY Token Piyasa Haberleri", aury_sentiment_results["token_news"])

        # Use Case 4: Oyuncu kazanç stratejileri ve token ekonomisi
        print("\n>>> KULLANIM SENARYOSU 4: Başarılı oyuncuların Twitter'da tartıştığı kazanç stratejileri ve mevcut token ekonomisi <<<")
        player_strategy_results = pipeline.get_player_earning_strategies(limit=3)
        print_search_results("Oyuncu Kazanç Stratejileri (Tweetler)", player_strategy_results["player_strategy_tweets"])
        print_search_results("Token Ekonomisi Bilgisi (Haberler)", player_strategy_results["token_economy_news"])

        # Use Case 5: Aurory ekosistemi ana ekonomik riskleri
        print("\n>>> KULLANIM SENARYUSU 5: Aurory ekosistemi için ana ekonomik riskler <<<")
        ecosystem_risk_results = pipeline.get_ecosystem_economic_risks(limit=3)
        print_search_results("Ekonomik Risk Haberleri", ecosystem_risk_results["risk_news"])
        print_search_results("Topluluk Risk Tartışmaları (Tweetler)", ecosystem_risk_results["risk_tweets"])

    finally:
        # Program sonunda Neo4j bağlantısını kapat
        pipeline.close_connection()

if __name__ == "__main__":
    main()
