# graph.py
import os
from langchain_neo4j import Neo4jGraph
from neo4j import GraphDatabase # <-- YENİ EKLENDİ: neo4j driver'ını import et

# Neo4j bağlantı bilgileri
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password") # <-- BURAYI GÜNCELLEYİN

# Global driver ve graph objelerini tanımla
driver = None
graph = None

try:
    # Temel Neo4j driver objesini oluştur
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity() # Bağlantıyı doğrula
    print("✅ Neo4j database driver initialized successfully.")

    # Langchain için Neo4jGraph nesnesi oluştur
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD
    )
    # Langchain graph bağlantısını test et (isteğe bağlı)
    _ = graph.query("RETURN 1 as test") # Basit bir sorgu ile test
    print("✅ LangChain Neo4jGraph connection successful.")

except Exception as e:
    print(f"❌ Neo4j connection failed: {e}")
    # Hata durumunda, driver ve graph objelerini None yap veya hata mesajı döndür
    driver = None
    graph = None # Langchain graph nesnesi de başarısız olur

# Dışa aktarılacak objeler
__all__ = ['graph', 'driver'] # <-- YENİ EKLENDİ: 'driver'ı da dışa aktar