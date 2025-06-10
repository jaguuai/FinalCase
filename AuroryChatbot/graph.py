import streamlit as st
from langchain_neo4j import Neo4jGraph

# Neo4j bağlantı bilgileri st.secrets'tan çekiliyor
NEO4J_URI = st.secrets["NEO4J_URI"]
NEO4J_USERNAME = st.secrets["NEO4J_USERNAME"]
NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]

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