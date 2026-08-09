import streamlit as st
from openai import OpenAI

# 1. Konfigurasi Tampilan Halaman
st.set_page_config(
    page_title="AI Teknisi Service TV", 
    page_icon="🔧",
    initial_sidebar_state="collapsed"
)

# Style CSS: Sembunyikan tombol/menu bawaan Streamlit & buat footer khusus yang rapi
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    /* Beri jarak bawah agar isi chat tidak tertutup footer */
    .block-container {
        padding-bottom: 70px;
    }
    
    /* Tampilan Footer Copyright kustom */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: #888888;
        text-align: center;
        padding: 8px;
        font-size: 12px;
        border-top: 1px solid #262730;
        z-index: 99;
    }
    </style>
    <div class="custom-footer">
        © 2026 <b>Rasmuhammad</b>. All Rights Reserved | AI Teknisi Service TV
    </div>
    """,
    unsafe_allow_html=True
)

st.title("🔧 ASISTEN TEKNISI ELEKTRONIK & SERVICE TV")
st.caption("Siap membantu diagnosa kerusakan TV LED, LCD, Tabung, dan Smart TV")

# 2. Inisialisasi OpenAI Client
client = OpenAI()

# 3. Inisialisasi Memori Percakapan
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Kamu adalah Asisten Senior Teknisi Elektronik dan Perbaikan TV. "
                "Tugasmu membantu teknisi menganalisis kerusakan perangkat.\n\n"
                "Panduan:\n"
                "1. Analisis gejala kerusakan.\n"
                "2. Sebutkan komponen berpotensi rusak (Power Supply, Backlight, T-Con, IC Vertical, dll).\n"
                "3. Berikan alur pengecekan tegangan/komponen.\n"
                "4. Selalu ingatkan KESELAMATAN KERJA.\n"
                "5. Gunakan bahasa teknis yang jelas."
            )
        }
    ]

# 4. Sidebar Pengaturan
st.sidebar.title("⚙️ Pengaturan")
st.sidebar.write("Pengembang: **Rasmuhammad**")

if st.sidebar.button("🔄 Reset Diagnosa"):
    st.session_state.messages = [st.session_state.messages[0]]
    st.rerun()

# 5. Tampilkan Riwayat Chat
for msg in st.session_state.messages:
    if msg["role"] != "system":
        avatar = "👨‍🔧" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

# 6. Input Pesan Pengguna
if prompt := st.chat_input("Ketik keluhan kerusakan (misal: TV LG LED gambar gelap suara ada)..."):
    with st.chat_message("user", avatar="👨‍🔧"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Menganalisis kerusakan..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                jawaban = response.choices[0].message.content
                st.markdown(jawaban)
                
                st.session_state.messages.append({"role": "assistant", "content": jawaban})
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
