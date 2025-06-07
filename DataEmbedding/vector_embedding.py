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
load_dotenv("C:/Users/alice/OneDrive/Masaüstü/FinalCase/neo4j.env")

class VectorEmbeddingPipeline:
    def __init__(self):
        """
        OpenAI kullanarak .env değişkenleri ile vektör gömme hattı
        """
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, 
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      # Her metin parçasının maksimum boyutu
            chunk_overlap=200,    # Parçalar arasındaki çakışma miktarı (bağlamı korumak için)
            length_function=len,  # Uzunluk hesaplama fonksiyonu (karakter sayısı)
        )

    def test_connection(self) -> bool:
        """Neo4j bağlantısını test eder."""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) RETURN n LIMIT 1") # Basit bir sorgu ile bağlantıyı test et
                print("✅ Neo4j bağlantı testi: Başarılı!")
            return True
        except Exception as e:
            print(f"❌ Neo4j bağlantı hatası: {str(e)}")
            traceback.print_exc()
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
                # Sadece .csv uzantılı dosyaları işle
                if not csv_file.lower().endswith('.csv'):
                    print(f"⚠️ Atlandı: '{csv_file}' bir CSV dosyası değil.")
                    continue

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
                
                # Tweet'i ekonomik açıdan analiz eder (sadece tokenlar)
                economy_analysis = self.analyze_tweet_economy(content)
                # Tweet'in ekonomik etkisini değerlendirir
                impact_score = self.assess_tweet_impact(content, economy_analysis)
                
                # Meta verileri oluşturur
                metadata = {
                    "source": source_file,
                    "doc_type": "tweet",
                    "tweet_id": row.get('id', ''),
                    "author": row.get('author', ''),
                    # LIKES VE RETWEETS KALDIRILDI
                    "date": row.get('date', ''),
                    "tokens": economy_analysis.get('tokens', []), # Bahsedilen tokenlar
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
        # 'nft' ile ilgili sınıflandırma kaldırıldı
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
        
        return score

    def analyze_tweet_economy(self, tweet_text: str) -> Dict[str, Any]:
        """
        Bir tweet'in ekonomik içeriğini (sadece bahsedilen tokenlar) analiz eder.
        """
        tweet_lower = tweet_text.lower()
        
        # Aurory ekosistemine özgü token isimleri
        token_keywords = ['aury', 'aurory', 'token', 'coin', 'xaury', 'nerite', 'ember', 'wisdom']
        found_tokens = [token for token in token_keywords if token in tweet_lower]
        
        return {
            'tokens': list(set(found_tokens)), # Tekrar edenleri kaldır
            'has_economic_content': len(found_tokens) > 0 # Sadece tokenlar varsa ekonomik içerik var say
        }

    def assess_tweet_impact(self, tweet_text: str, economy_analysis: Dict[str, Any]) -> int:
        """Bir tweet'in ekonomik etkisini değerlendirir."""
        tweet_lower = tweet_text.lower()
        score = 1
        
        # Ekonomik içerik varsa temel skoru artır
        if economy_analysis.get('has_economic_content', False):
            score = 2
        
        # Yüksek etkili kelimeler için puan artır
        high_impact_words = ['price', 'market', 'value', 'pump', 'dump', 'bullish', 'bearish', 'risk', 'exploit']
        for word in high_impact_words:
            if word in tweet_lower:
                score = min(5, score + 1)
        
        # Duygu analizi (basit anahtar kelime tabanlı)
        positive_words = ['good', 'great', 'buy', 'strong', 'up', 'moon', ' bullish']
        negative_words = ['bad', 'sell', 'weak', 'down', 'bearish', 'scam', 'rug pull']
        
        for word in positive_words:
            if word in tweet_lower:
                score = min(5, score + 1)
        for word in negative_words:
            if word in tweet_lower:
                score = max(1, score - 1) # Skoru 1'in altına düşürme
        
        return score

    def store_documents_in_neo4j(self, documents: List[Document]):
        """
        İşlenen belgeleri Neo4j'ye kaydeder ve vektör indeksini oluşturur.
        """
        print(f"\n--- {len(documents)} belge Neo4j'ye yazılıyor... ---")
        try:
            # LangChain'in Neo4jVector sınıfını kullanarak belgeleri kaydeder
            Neo4jVector.from_documents(
                documents,
                self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name="aurory_docs",
                node_label="Document",
                text_node_property="content",
                embedding_node_property="embedding",
            )
            print("✅ Tüm belgeler Neo4j'ye başarıyla yazıldı ve vektör indeksi oluşturuldu.")
        except Exception as e:
            print(f"❌ Belgeleri Neo4j'ye kaydetme hatası: {str(e)}")
            traceback.print_exc()

    def create_document_relationships(self):
        """
        Neo4j'deki Document düğümleri ile diğer düğümler (Token, Proposal, GameMechanic) arasında
        ilişkiler oluşturur.
        """
        print("\n--- Belge ilişkileri oluşturuluyor... ---")
        try:
            with self.driver.session() as session:
                # 1. DAO Proposal ile ilişkiler (Mevcut haliyle kalsın)
                query_dao = """
                MATCH (d:Document)
                WHERE d.doc_type = 'dao_proposal' AND d.proposal_id IS NOT NULL
                MERGE (p:Proposal {proposalId: d.proposal_id})
                ON CREATE SET p.title = 'Öneri #' + d.proposal_id // Başlık yoksa varsayılan başlık
                MERGE (d)-[:DESCRIBES]->(p)
                """
                session.run(query_dao)
                print("✅ DAO Proposal-Document bağlantıları kuruldu (:DESCRIBES)")

                # 2. Token ile ilişkiler (tweetler ve haberler için)
                # :DISCUSSES - genel olarak bahsedilen tokenlar
                query_token_discusses = """
                MATCH (d:Document)
                WHERE d.doc_type IN ['tweet', 'news'] AND d.tokens IS NOT NULL
                UNWIND d.tokens AS tokenName
                MATCH (t:Token)
                WHERE toLower(t.name) CONTAINS toLower(tokenName) OR toLower(t.symbol) CONTAINS toLower(tokenName)
                MERGE (d)-[:DISCUSSES]->(t)
                """
                session.run(query_token_discusses)
                print("✅ Tweet/News-Token bağlantıları kuruldu (:DISCUSSES)")

                # :AFFECTS - haberler için (Ekonomik Önem > 2 olanlar)
                query_token_affects_news = """
                MATCH (d:Document)
                WHERE d.doc_type = 'news' AND d.economic_significance >= 2 AND d.tokens IS NOT NULL
                UNWIND d.tokens AS tokenName
                MATCH (t:Token)
                WHERE toLower(t.name) CONTAINS toLower(tokenName) OR toLower(t.symbol) CONTAINS toLower(tokenName)
                MERGE (d)-[:AFFECTS]->(t)
                """
                session.run(query_token_affects_news)
                print("✅ News-Token bağlantıları kuruldu (:AFFECTS) [Ekonomik Önem >= 2]")
                
                # :POTENTIAL_IMPACT - tweetler için (Ekonomik Önem > 3 olanlar)
                query_token_potential_impact_tweet = """
                MATCH (d:Document)
                WHERE d.doc_type = 'tweet' AND d.economic_significance >= 3 AND d.tokens IS NOT NULL
                UNWIND d.tokens AS tokenName
                MATCH (t:Token)
                WHERE toLower(t.name) CONTAINS toLower(tokenName) OR toLower(t.symbol) CONTAINS toLower(tokenName)
                MERGE (d)-[:POTENTIAL_IMPACT]->(t)
                """
                session.run(query_token_potential_impact_tweet)
                print("✅ Tweet-Token bağlantıları kuruldu (:POTENTIAL_IMPACT) [Ekonomik Önem >= 3]")


                # Haberler ile GameMechanic İlişkileri
                # Haber içeriğindeki GameMechanic anahtar kelimelerini kullanarak ilişkilendirme
                game_mechanics = session.run("MATCH (gm:GameMechanic) RETURN gm.name AS name").data()
                game_mechanic_names = [gm['name'].lower() for gm in game_mechanics if gm['name']]

                if game_mechanic_names:
                    # Dinamik olarak sorguyu oluştur
                    # Bu sorgu her bir haber dokümanı için GameMechanic adlarını kontrol eder.
                    # Eğer doküman içeriğinde GameMechanic adı geçiyorsa ilişki kurar.
                    query_news_game_mechanic = f"""
                    MATCH (d:Document)
                    WHERE d.doc_type = 'news'
                    UNWIND {game_mechanic_names} AS gmName
                    MATCH (gm:GameMechanic)
                    WHERE toLower(gm.name) = gmName AND toLower(d.content) CONTAINS gmName
                    MERGE (d)-[:DISCUSSES_MECHANIC]->(gm)
                    """
                    session.run(query_news_game_mechanic)
                    print(f"✅ News-GameMechanic bağlantıları kuruldu (:DISCUSSES_MECHANIC) for {len(game_mechanic_names)} mechanics.")
                else:
                    print("⚠️ Neo4j'de hiç GameMechanic bulunamadı, News-GameMechanic ilişkisi oluşturulmadı.")


                # Tweetler ile Proposal İlişkileri (Duygu ile birlikte)
                # Tweet metadata'sındaki proposal_id'yi kullanarak ilişkilendirme
                query_tweet_proposal_sentiment = """
                MATCH (d:Document)
                WHERE d.doc_type = 'tweet' AND d.proposal_id IS NOT NULL
                MATCH (p:Proposal {proposalId: d.proposal_id})
                MERGE (d)-[r:DISCUSSES_PROPOSAL]->(p)
                SET r.sentiment_score = d.economic_significance // Tweet'in ekonomik önemini duygu skoru olarak kullan
                """
                session.run(query_tweet_proposal_sentiment)
                print("✅ Tweet-Proposal bağlantıları kuruldu (:DISCUSSES_PROPOSAL) [Duygu Skoru ile]")

            print("✅ Tüm belge ilişkileri başarıyla oluşturuldu.")
        except Exception as e:
            print(f"❌ Belge ilişkileri oluşturma hatası: {str(e)}")
            traceback.print_exc()

    def semantic_search(self, query_text: str, limit: int = 5, filters: Dict[str, Any] = None, score_threshold: float = 0.65) -> List[Document]:
        """
        Belirtilen sorgu metnine göre anlamsal arama yapar ve isteğe bağlı filtreler uygular.
        score_threshold: Döndürülecek dokümanların sahip olması gereken minimum benzerlik puanı.
        """
        try:
            # Neo4jVector nesnesini oluştur, burada retrieval_query'ye karmaşık WHERE clause koymuyoruz.
            # Sadece temel döndürme sorgusu ve index bilgileri ile oluşturuyoruz.
            vector_store = Neo4jVector.from_existing_index(
                embedding=self.embedding_model,
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                index_name="aurory_docs",
                text_node_property="content",
                embedding_node_property="embedding",
                # retrieval_query burada daha basit olabilir, sadece ne döndürüleceğini belirtir.
                # Filtreleri Python tarafında uygulayacağız.
                retrieval_query="""
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
                        // LIKES VE RETWEETS KALDIRILDI
                        tokens: node.tokens
                    } AS metadata
                """
            )

            # Benzerlik araması yapar. İlk olarak daha fazla aday alıyoruz (limit * 5 veya daha fazla),
            # çünkü filtreleme sonrası yeterli sonuç kalmayabilir.
            # Bu kısım sadece vektör benzerliğine göre çalışır.
            docs_and_scores = vector_store.similarity_search_with_score(query_text, k=limit * 5) # Yeterli aday almak için k'yı artır

            filtered_results = []
            for doc, score in docs_and_scores:
                # Önce skor eşiğini kontrol et
                if score < score_threshold:
                    continue

                # Ardından Python içinde meta veri filtrelerini uygula
                metadata = doc.metadata
                match_filters = True

                if filters:
                    if "doc_type" in filters and filters["doc_type"] is not None:
                        if metadata.get("doc_type") != filters["doc_type"]:
                            match_filters = False
                    
                    if match_filters and "economic_significance_min" in filters and filters["economic_significance_min"] is not None:
                        if metadata.get("economic_significance", 0) < filters["economic_significance_min"]:
                            match_filters = False
                    
                    if match_filters and "proposal_id" in filters and filters["proposal_id"] is not None:
                        # proposal_id'nin tipini kontrol et, string veya int olabilir
                        if str(metadata.get("proposal_id")) != str(filters["proposal_id"]):
                            match_filters = False
                    
                    if match_filters and "author" in filters and filters["author"] is not None:
                        if filters["author"].lower() not in metadata.get("author", "").lower():
                            match_filters = False
                    
                    if match_filters and "tokens_mentioned" in filters and filters["tokens_mentioned"] is not None:
                        # Metadata'daki 'tokens' listesini kontrol et
                        doc_tokens = [t.lower() for t in metadata.get("tokens", [])]
                        if not any(token.lower() in doc_tokens for token in filters["tokens_mentioned"]):
                            match_filters = False
                    
                if match_filters:
                    filtered_results.append(doc)
                
                if len(filtered_results) >= limit: # İstenilen limite ulaşıldığında dur
                    break
            
            return filtered_results
        except Exception as e:
            print(f"❌ Semantic search hatası: {str(e)}")
            traceback.print_exc()
            return []

    def get_dao_proposal_info(self, proposal_id: str, limit: int = 5) -> Dict[str, List[Document]]:
        """
        Belirli bir DAO önerisi için ilgili belgeleri ve topluluk tepkisini getirir.
        """
        print(f"\n--- DAO Önerisi '{proposal_id}' için arama başlatılıyor ---")
        results = {}

        # DAO önerisi ile ilgili belgeleri arar
        proposal_query = f"DAO Proposal {proposal_id} details and community discussion."
        proposal_filters = {"doc_type": "dao_proposal", "proposal_id": proposal_id}
        proposal_docs = self.semantic_search(proposal_query, limit=limit, filters=proposal_filters)
        results["proposal_docs"] = proposal_docs
        print(f"✅ {len(proposal_docs)} adet DAO önerisi dokümanı bulundu.")

        # Bu öneri hakkındaki tweetleri arar (topluluk tepkisi için)
        tweet_query = f"Community sentiment, discussion, and engagement on DAO Proposal {proposal_id} on Twitter."
        tweet_filters = {"doc_type": "tweet", "proposal_id": proposal_id, "economic_significance_min": 1}
        proposal_tweets = self.semantic_search(tweet_query, limit=limit, filters=tweet_filters)
        results["proposal_tweets"] = proposal_tweets
        print(f"✅ {len(proposal_tweets)} adet DAO önerisi tweet'i bulundu.")

        return results

    def get_token_market_sentiment(self, token_name: str, limit: int = 5) -> Dict[str, List[Document]]:
        """
        Belirli bir token için piyasa duyarlılığını ve ilgili sosyal medya/haberleri getirir.
        """
        print(f"\n--- Token '{token_name}' için piyasa duyarlılığı ve haber arama başlatılıyor ---")
        results = {}

        # Token ile ilgili tweet'leri arar
        tweet_query = f"Market sentiment, price discussion, and social media buzz about {token_name} token."
        tweet_filters = {"doc_type": "tweet", "tokens_mentioned": [token_name.lower()], "economic_significance_min": 1}
        token_tweets = self.semantic_search(tweet_query, limit=limit, filters=tweet_filters)
        results["token_tweets"] = token_tweets
        print(f"✅ {len(token_tweets)} adet '{token_name}' ile ilgili tweet bulundu.")

        # Token ile ilgili haberleri arar
        news_query = f"Market analysis, price movements, and news about {token_name} token."
        news_filters = {"doc_type": "news", "tokens_mentioned": [token_name.lower()], "economic_significance_min": 2}
        token_news = self.semantic_search(news_query, limit=limit, filters=news_filters)
        results["token_news"] = token_news
        print(f"✅ {len(token_news)} adet '{token_name}' ile ilgili haber bulundu.")

        return results

    def get_player_earning_strategies(self, limit: int = 5) -> Dict[str, List[Document]]:
        """
        Başarılı oyuncuların tartıştığı kazanç stratejilerini ve token ekonomisiyle ilgili bilgileri getirir.
        """
        print("\n>>> Oyuncu kazanç stratejileri ve token ekonomisi arama başlatılıyor <<<")
        results = {}

        # Oyuncu stratejileri ile ilgili tweetleri ara
        strategy_tweet_query = "Successful player earning strategies, tips, and gameplay tactics in Aurory."
        strategy_tweet_filters = {"doc_type": "tweet", "economic_significance_min": 2} # Strateji odaklı tweetler
        player_strategy_tweets = self.semantic_search(strategy_tweet_query, limit=limit, filters=strategy_tweet_filters)
        results["player_strategy_tweets"] = player_strategy_tweets
        print(f"✅ {len(player_strategy_tweets)} adet oyuncu stratejisi tweet'i bulundu.")

        # Token ekonomisi ve oyun içi ekonomik bilgilerle ilgili haberleri ara
        token_economy_news_query = "Aurory tokenomics, in-game economy, earning mechanisms, and game token utility."
        token_economy_news_filters = {"doc_type": "news", "economic_significance_min": 3, "event_type": "tokenomics"}
        token_economy_news = self.semantic_search(token_economy_news_query, limit=limit, filters=token_economy_news_filters)
        results["token_economy_news"] = token_economy_news
        print(f"✅ {len(token_economy_news)} adet token ekonomisi haberi bulundu.")

        return results

    def get_ecosystem_economic_risks(self, limit: int = 5) -> Dict[str, List[Document]]:
        """
        Aurory ekosistemi için ana ekonomik riskleri ve ilgili tartışmaları getirir.
        """
        print("\n>>> Aurory ekosistemi ekonomik riskleri arama başlatılıyor <<<")
        results = {}

        # Ekonomik risklerle ilgili haberleri ara
        risk_news_query = "Economic risks, vulnerabilities, market threats, and stability concerns for Aurory ecosystem."
        risk_news_filters = {"doc_type": "news", "economic_significance_min": 3} # Yüksek ekonomik önem taşıyan risk haberleri
        risk_news = self.semantic_search(risk_news_query, limit=limit, filters=risk_news_filters)
        results["risk_news"] = risk_news
        print(f"✅ {len(risk_news)} adet ekonomik risk haberi bulundu.")

        # Toplulukta risk tartışmaları ile ilgili tweetleri ara
        community_risk_tweet_query = "Community concerns, FUD, security issues, and economic warnings about Aurory."
        community_risk_tweet_filters = {"doc_type": "tweet", "economic_significance_min": 2} # Orta/yüksek ekonomik önem taşıyan topluluk tartışmaları
        community_risk_tweets = self.semantic_search(community_risk_tweet_query, limit=limit, filters=community_risk_tweet_filters)
        results["community_risk_tweets"] = community_risk_tweets
        print(f"✅ {len(community_risk_tweets)} adet topluluk risk tartışması tweet'i bulundu.")

        return results

def print_search_results(title: str, results: List[Document]):
    """Arama sonuçlarını düzenli bir şekilde yazdırır."""
    print(f"\n--- {title} ---")
    if not results:
        print("Sonuç bulunamadı.")
        return

    for i, doc in enumerate(results):
        print(f"Sonuç {i+1}:")
        print(f"  Kaynak: {doc.metadata.get('source', 'Bilinmiyor')}")
        print(f"  Tip: {doc.metadata.get('doc_type', 'Bilinmiyor')}")
        if 'title' in doc.metadata:
            print(f"  Başlık: {doc.metadata['title']}")
        if 'tweet_id' in doc.metadata:
            print(f"  Tweet ID: {doc.metadata['tweet_id']}")
        if 'author' in doc.metadata:
            print(f"  Yazar: {doc.metadata['author']}")
        # LIKES VE RETWEETS ÇIKTI KALDIRILDI
        if 'proposal_id' in doc.metadata:
            print(f"  Öneri ID: {doc.metadata['proposal_id']}")
        if 'economic_significance' in doc.metadata:
            print(f"  Ekonomik Önem: {doc.metadata['economic_significance']}")
        if 'tokens' in doc.metadata and doc.metadata['tokens']:
            print(f"  Bahsedilen Tokenlar: {', '.join(doc.metadata['tokens'])}")
        print(f"  İçerik Özeti: {doc.page_content[:200]}...") # İlk 200 karakteri göster
        print("-" * 30)

if __name__ == "__main__":
    pipeline = VectorEmbeddingPipeline()

    # Neo4j bağlantısını test et
    if not pipeline.test_connection():
        print("Uygulama Neo4j bağlantısı olmadan devam edemez.")
        exit()

    # Veri yükleme ve işleme
    pdf_folder = "C:/Users/alice/OneDrive/Masaüstü/FinalCase/DataGathering/embedding_data/DAOPDF"
    csv_files = [
        "C:/Users/alice/OneDrive/Masaüstü/FinalCase/DataGathering/embedding_data/news.csv",
        "C:/Users/alice/OneDrive/Masaüstü/FinalCase/DataGathering/embedding_data/tweets.csv" 
    ]

    all_documents = []

    # PDF belgelerini işle
    pdf_docs = pipeline.process_pdf_documents(pdf_folder)
    all_documents.extend(pdf_docs)

    # CSV verilerini işle
    csv_docs = pipeline.process_csv_data(csv_files)
    all_documents.extend(csv_docs)

    if all_documents:
        # Belgeleri Neo4j'ye kaydet ve vektör indeksini oluştur
        pipeline.store_documents_in_neo4j(all_documents)
        # Belgeler arasında ilişkileri oluştur
        pipeline.create_document_relationships()
    else:
        print("İşlenecek belge bulunamadı. Vektör indeksleme ve ilişki oluşturma atlanıyor.")

    # Arama Örnekleri (Kullanım Senaryoları)
    print("\n\n>>> ARAMA ÖRNEKLERİ BAŞLIYOR <<<")

    # Use Case 1: DAO önerisi ve topluluk tepkisi
    print("\n>>> KULLANIM SENARYOSU 1: Belirli bir DAO önerisi için belgeler ve topluluk tepkisi <<<\n")
    dao_results = pipeline.get_dao_proposal_info(proposal_id="7", limit=3) # Örnek bir öneri ID'si
    print_search_results("DAO Önerisi Dokümanları", dao_results["proposal_docs"])
    print_search_results("DAO Önerisi Topluluk Tweetleri", dao_results["proposal_tweets"])

    # Use Case 2: Token piyasa duyarlılığı
    print("\n>>> KULLANIM SENARYOSU 2: AURY Token Piyasa Duyarlılığı <<<\n")
    # score_threshold'u örnek olarak 0.55'e düşürerek daha fazla eşleşme yakalamayı deneyelim
    aury_sentiment_results = pipeline.get_token_market_sentiment("AURY", limit=3)
    print_search_results("AURY Token Twitter Duyarlılığı", aury_sentiment_results["token_tweets"])
    print_search_results("AURY Token Piyasa Haberleri", aury_sentiment_results["token_news"])

    # Use Case 4: Oyuncu kazanç stratejileri ve token ekonomisi
    print("\n>>> KULLANIM SENARYOSU 4: Başarılı oyuncuların Twitter'da tartıştığı kazanç stratejileri ve mevcut token ekonomisi <<<\n")
    player_strategy_results = pipeline.get_player_earning_strategies(limit=3)
    print_search_results("Oyuncu Kazanç Stratejileri (Tweetler)", player_strategy_results["player_strategy_tweets"])
    print_search_results("Token Ekonomisi Bilgisi (Haberler)", player_strategy_results["token_economy_news"])

    # Use Case 5: Aurory ekosistemi ana ekonomik riskleri
    print("\n>>> KULLANIM SENARYOSU 5: Aurory ekosistemi için ana ekonomik riskler <<<\n")
    ecosystem_risk_results = pipeline.get_ecosystem_economic_risks(limit=3)
    print_search_results("Ekonomik Risk Haberleri", ecosystem_risk_results["risk_news"])
    print_search_results("Topluluk Risk Tartışmaları (Tweetler)", ecosystem_risk_results["community_risk_tweets"])