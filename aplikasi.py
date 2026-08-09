import re
import os
import streamlit as st
from openai import OpenAI

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN & TAMPILAN (UI)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Service TV Pro - Asisten Teknisi",
    page_icon="📺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Force environment encoding ke UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Style CSS Kustom & Footer Professional
st.markdown(
    """
    <style>
    /* Sembunyikan elemen bawaan Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    /* Atur padding bawah agar chat tidak tertutup footer */
    .block-container {
        padding-bottom: 90px;
    }
    
    /* Footer Profesional & Sticky */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: #999999;
        text-align: center;
        padding: 12px 0;
        font-size: 13px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        border-top: 1px solid #262730;
        z-index: 999;
    }
    .custom-footer b {
        color: #ffffff;
    }
    </style>
    
    <div class="custom-footer">
        © 2026 <b>Rasmuhammad</b>. All Rights Reserved. | <b>AI Service TV Pro v2.0</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📺 AI TEKNISI & SERVICE TV PRO")
st.caption("Sistem Pakar Diagnosa Kerusakan TV LED, LCD, OLED, Plasma, & TV Tabung")

# -----------------------------------------------------------------------------
# 2. INISIALISASI OPENAI CLIENT
# -----------------------------------------------------------------------------
client = OpenAI()

# -----------------------------------------------------------------------------
# 3. SYSTEM PROMPT (INSTRUKSI AI TEKNISI)
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "Kamu adalah Asisten Senior Teknisi Elektronik dan Perbaikan TV Profesional.\n"
    "Tugasmu membantu teknisi menganalisis kerusakan perangkat secara akurat.\n\n"
    "Format Jawaban Wajib:\n"
    "1. **Analisis Gejala**: Ringkasan masalah utama.\n"
    "2. **Komponen Suspek**: Sebutkan komponen berpotensi rusak (Power Supply/PSU, Mainboard, T-Con, Backlight, IC Vertical, Panel, dll).\n"
    "3. **Langkah Pemeriksaan**: Panduan pengujian titik ukur tegangan (VCC, VGH, VGL, B+, dll) dan fisik komponen.\n"
    "4. **Prosedur Keselamatan**: Peringatan bahaya tegangan tinggi (kapasitor utama/flyback).\n"
    "Gunakan bahasa teknis bengkel yang lugas, padat, dan mudah dipahami."
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# -----------------------------------------------------------------------------
# 4. SIDEBAR PENGATURAN
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    st.write("Pengembang: **Rasmuhammad**")
    st.write("Status Sistem: 🟢 **Aktif**")
    st.markdown("---")
    
    if st.button("🗑️ Reset Sesi Diagnosa", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

# -----------------------------------------------------------------------------
# 5. RIWAYAT CHAT
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        avatar_icon = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.markdown(msg["content"])

# -----------------------------------------------------------------------------
# 6. INPUT USER & SANITASI TEKS (KEAMANAN DARI EROR ASCII/WORD)
# -----------------------------------------------------------------------------
if raw_prompt := st.chat_input("Ketik keluhan kerusakan (Contoh: TV Sharp LED suara ada gambar gelap)..."):
    
    # A. Saring & buang karakter non-ASCII tersembunyi (\u200e dll)
    clean_prompt = raw_prompt.encode('ascii', errors='ignore').decode('ascii')
    
    # B. Pembersihan ekstra dengan Regex untuk karakter formatting
    clean_prompt = re.sub(r'[\u200b-\u200d\ufeff\u200e\u200f]', '', clean_prompt).strip()

    # C. Jika setelah dibersihkan teks tidak kosong
    if clean_prompt:
        # Tampilkan pesan user
        with st.chat_message("user", avatar="👤"):
            st.markdown(clean_prompt)
        
        st.session_state.messages.append({"role": "user", "content": clean_prompt})

        # Proses jawaban AI
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Menganalisis skema & gejala kerusakan..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages
                    )
                    jawaban = response.choices[0].message.content
                    
                    st.markdown(jawaban)
                    st.session_state.messages.append({"role": "assistant", "content": jawaban})
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan pada sistem: {e}")
