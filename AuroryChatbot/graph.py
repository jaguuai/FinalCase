import os
from langchain_neo4j import Neo4jGraph

# Neo4j bağlantı bilgileri
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

try:
    # Neo4j Graph nesnesi oluştur
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD
    )
    
    # Bağlantı testi
    test_result = graph.query("RETURN 1 as test")
    print("✅ Neo4j connection successful")
    
except Exception as e:
    print(f"❌ Neo4j connection failed: {e}")
    # Hata durumunda string döndür (bu durumu cypher.py'de yakalıyoruz)
    graph = f"Connection failed: {str(e)}"

# Export the graph object
__all__ = ['graph']