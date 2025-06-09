from datetime import datetime
import os
import uuid
import streamlit as st

# graph.py dosyasından driver'ı import et
from graph import driver # <-- BURASI DEĞİŞTİ

def close_neo44j_history_driver():
    """
    Bu fonksiyon artık gerekli değil çünkü driver graph.py tarafından yönetiliyor.
    Ancak yine de uygulamadan çıkışta driver'ı kapatmak için graph.py'deki
    driver.close() metodunu çağıran bir mekanizma kurmanız iyi olur.
    """
    # Bu fonksiyonun içeriğini silebiliriz, veya bilgilendirici bir mesaj bırakabiliriz.
    print("history.py: Driver kapatma işlemi graph.py tarafından yönetiliyor.")


# --- Function to Save Snapshot to Neo4j ---
def save_current_chat_to_neo4j(session_messages, session_id):
    """
    Saves the current chat session from session_messages to Neo4j.
    Each message (user and assistant) will be a separate ChatMessage node
    linked to a UserSession node.
    """
    global driver # <-- ÖNEMLİ: Global driver'ı kullanacağımızı belirt
    if not driver: # Check if driver was initialized successfully by graph.py
        st.warning("Neo4j connection not established (from graph.py). Cannot save chat history.")
        return False
    
    if not session_messages:
        return False

    try:
        with driver.session() as session:
            # 1. Find or Create the UserSession node
            session_result = session.run(
                """
                MERGE (s:UserSession {sessionId: $sessionId})
                ON CREATE SET s.createdAt = datetime(), s.totalMessages = 0
                ON MATCH SET s.lastActive = datetime()
                RETURN s
                """,
                sessionId=session_id
            )
            
            # Get the current message count in Neo4j for ordering
            existing_message_count_result = session.run(
                """
                MATCH (s:UserSession {sessionId: $sessionId})-[:HAS_MESSAGE]->(m:ChatMessage)
                RETURN count(m) AS count
                """,
                sessionId=session_id
            )
            start_order_index = existing_message_count_result.single()["count"]

            prev_message_node_id = None # To link messages using :FOLLOWS

            # 2. Iterate through messages and create ChatMessage nodes
            for i, message_data in enumerate(session_messages):
                if i < start_order_index:
                    continue # Skip already saved messages if any

                message_id = message_data.get("id", str(uuid.uuid4()))
                role = message_data["role"]
                content = message_data["content"]
                timestamp_iso = message_data["timestamp"]
                timestamp_unix = int(datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00')).timestamp())
                agent_id = message_data.get("agent_id")
                
                query_details = message_data.get("query_details", {})
                generated_cypher_query = message_data.get("generated_cypher_query")

                create_message_query = """
                MATCH (s:UserSession {sessionId: $sessionId})
                CREATE (m:ChatMessage {
                    messageId: $messageId,
                    role: $role,
                    content: $content,
                    timestamp: $timestamp_unix,
                    timestamp_iso: $timestamp_iso,
                    agentId: $agentId,
                    processing_time: $processing_time,
                    tokens_used: $tokens_used,
                    confidence: $confidence,
                    agent_used_name: $agent_used_name,
                    generatedCypherQuery: $generatedCypherQuery,
                    orderInSession: $orderInSession
                })
                CREATE (s)-[:HAS_MESSAGE]->(m)
                RETURN m
                """
                
                result = session.run(
                    create_message_query,
                    sessionId=session_id,
                    messageId=message_id,
                    role=role,
                    content=content,
                    timestamp_unix=timestamp_unix,
                    timestamp_iso=timestamp_iso,
                    agentId=agent_id,
                    processing_time=query_details.get("processing_time"),
                    tokens_used=query_details.get("tokens_used"),
                    confidence=query_details.get("confidence"),
                    agent_used_name=query_details.get("agent_used"),
                    generatedCypher_query=generated_cypher_query,
                    orderInSession=start_order_index + i
                )
                
                current_message_node_id = result.single()["m"].id

                if prev_message_node_id is not None:
                    session.run(
                        f"""
                        MATCH (prev:ChatMessage) WHERE id(prev) = {prev_message_node_id}
                        MATCH (curr:ChatMessage) WHERE id(curr) = {current_message_node_id}
                        CREATE (prev)-[:FOLLOWS]->(curr)
                        """
                    )
                prev_message_node_id = current_message_node_id
            
            session.run(
                """
                MATCH (s:UserSession {sessionId: $sessionId})
                SET s.totalMessages = $newTotalMessages
                """,
                sessionId=session_id,
                newTotalMessages=start_order_index + len(session_messages)
            )

        st.success(f"Chat session {session_id[:8]}... saved to Neo4j!")
        return True
    except Exception as e:
        st.error(f"Error saving chat to Neo4j: {e}")
        print(f"Neo4j save error: {e}")
        return False

# Diğer yükleme fonksiyonları da benzer şekilde `driver` objesini kullanır.
def load_all_chat_sessions_from_neo4j():
    """
    Loads all distinct chat sessions (UserSession nodes) from Neo4j.
    """
    global driver # <-- ÖNEMLİ
    if not driver:
        return []

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:UserSession)
                RETURN s.sessionId AS id, s.createdAt AS timestamp, s.totalMessages AS totalMessages
                ORDER BY s.createdAt DESC
                LIMIT 50
            """)
            sessions_list = []
            for record in result:
                sessions_list.append({
                    "id": record["id"],
                    "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                    "total_messages": record["totalMessages"]
                })
            return sessions_list
    except Exception as e:
        st.error(f"Error loading chat sessions from Neo4j: {e}")
        print(f"Neo4j load sessions error: {e}")
        return []

def load_specific_chat_session_from_neo4j(session_id):
    """
    Loads all messages for a specific chat session from Neo4j.
    """
    global driver # <-- ÖNEMLİ
    if not driver:
        return []

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:UserSession {sessionId: $sessionId})-[:HAS_MESSAGE]->(m:ChatMessage)
                RETURN m
                ORDER BY m.orderInSession ASC, m.timestamp ASC
                """,
                sessionId=session_id
            )
            messages_list = []
            for record in result:
                msg_node = record["m"]
                msg = {
                    "id": msg_node.get("messageId"),
                    "role": msg_node.get("role"),
                    "content": msg_node.get("content"),
                    "timestamp": msg_node.get("timestamp_iso") or datetime.fromtimestamp(msg_node.get("timestamp")).isoformat(),
                    "agent_id": msg_node.get("agentId"),
                    "query_details": {
                        "processing_time": msg_node.get("processing_time"),
                        "tokens_used": msg_node.get("tokens_used"),
                        "confidence": msg_node.get("confidence"),
                        "agent_used": msg_node.get("agent_used_name")
                    },
                    "generated_cypher_query": msg_node.get("generatedCypherQuery")
                }
                messages_list.append(msg)
            return messages_list
    except Exception as e:
        st.error(f"Error loading specific chat session {session_id[:8]}... from Neo4j: {e}")
        print(f"Neo4j load specific session error: {e}")
        return []