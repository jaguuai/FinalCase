import streamlit as st
from utils import write_message
from agent import generate_response

# --- Sayfa yapılandırması ---
st.set_page_config(
    page_title="Aurory Chatbot",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ile Buton ve Arka Plan Stilini Özelleştir ---
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        border-radius: 12px;
        padding: 10px 24px;
        margin-top: 10px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stApp {
        background-color: #f0f2f6;
        color: #262730;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar Menü ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Aurory_Logo.svg/120px-Aurory_Logo.svg.png", width=120)
    st.title("Aurory Menü")
    page = st.radio("Sayfa Seçimi:", ["Chatbot", "Hakkında", "İletişim"])
    st.markdown("---")
    st.write("🎮 Aurory P2E Ekonomi ve Topluluk Asistanı")

# --- Chatbot Sayfası ---
if page == "Chatbot":
    # Session State Mesajları
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask me anything, Seeker—markets, votes, or Neftie power!"},
        ]

    # Mesaj yazdırma fonksiyonu, dışarıdan import edilen write_message yerine buraya koyabilirsin:
    def write_message(role, content, save=True):
        if role == "user":
            st.markdown(f"**You:** {content}")
        else:
            st.markdown(f"**AuroryBot:** {content}")
        if save:
            st.session_state.messages.append({"role": role, "content": content})

    # Submit handler
    def handle_submit(message):
        with st.spinner('Thinking...'):
            response = generate_response(message)
            write_message('assistant', response)

    # Önceki mesajları göster
    for msg in st.session_state.messages:
        write_message(msg['role'], msg['content'], save=False)

    # Kullanıcıdan input al
    if prompt := st.chat_input("Soru yaz, Aurory ile ilgili her şey..."):
        write_message('user', prompt)
        handle_submit(prompt)

    # Örnek buton
    if st.button("Bana Tıkla!"):
        st.success("Butona tıkladın! 🎉")
    else:
        st.info("Butona henüz basılmadı.")

# --- Hakkında Sayfası ---
elif page == "Hakkında":
    st.title("Hakkında")
    st.markdown(
        """
        Bu Aurory Chatbot, oyun içi ekonomi, DAO kararları ve NFT pazarı hakkında canlı bilgiler sağlar.
        Token fiyatları, oylamalar ve topluluk analizleri için tasarlanmıştır.
        """
    )

# --- İletişim Sayfası ---
elif page == "İletişim":
    st.title("İletişim")
    st.markdown(
        """
        **E-posta:** support@aurorygame.com  
        **Discord:** discord.gg/aurory  
        **Twitter:** @aurorygame  
        """
    )
