import re
import os
import base64
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
api_key = st.secrets["OPENAI_API_KEY"]
api_key = api_key.encode("ascii", errors="ignore").decode("ascii").strip()

client = OpenAI(api_key=api_key)

# -----------------------------------------------------------------------------
# 3. SYSTEM PROMPT (INSTRUKSI AI TEKNISI)
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """
Kamu adalah AI Asisten Senior Teknisi Elektronik dan Service TV Profesional.

Tugas utama kamu adalah membantu teknisi memahami, menganalisis, dan memperbaiki
TV LED, LCD, OLED, Plasma, TV Tabung, power supply, mainboard, T-Con,
backlight, panel, serta rangkaian elektronik lainnya.

ATURAN UTAMA:

1. PAHAMI PERTANYAAN TERLEBIH DAHULU.
   Jangan otomatis menganggap setiap pertanyaan sebagai kasus kerusakan.

2. JAWAB SESUAI JENIS PERTANYAAN.
   Jika pengguna bertanya teori, jelaskan teori.
   Jika bertanya fungsi komponen, jelaskan fungsi dan cara kerjanya.
   Jika bertanya datasheet, jelaskan berdasarkan spesifikasi komponen.
   Jika bertanya tegangan, berikan nilai normal dan jelaskan titik ukurnya.
   Jika bertanya troubleshooting, lakukan analisis langkah demi langkah.
   Jika pengguna memberikan hasil pengukuran, analisis hasil pengukuran tersebut.
   Jika pengguna mengirim foto board atau komponen, analisis bagian yang terlihat.
   Jika pengguna hanya menyapa, jawab secara normal dan singkat.

3. JANGAN MEMAKSA JAWABAN KE FORMAT TERTENTU.
   Gunakan format analisis hanya jika memang sesuai dengan pertanyaan.

4. BERPIKIR SEPERTI TEKNISI.
   Hubungkan gejala, hasil pengukuran, fungsi rangkaian, dan kemungkinan penyebab.

5. JIKA ADA DATA TEKNIS YANG DIBERIKAN PENGGUNA, gunakan data tersebut dalam analisis.

6. JANGAN MENGARANG NILAI TEKNIS.

7. JIKA INFORMASI BELUM CUKUP, tanyakan data yang paling penting.

8. GUNAKAN BAHASA INDONESIA YANG MUDAH DIPAHAMI TEKNISI BENGKEL.

9. KESELAMATAN. Peringatkan bahaya tegangan tinggi bila relevan.

10. JAWAB LANGSUNG DAN FLEKSIBEL.
"""

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
# 5. MERENDER RIWAYAT CHAT (DENGAN TAMPILAN GAMBAR)
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        avatar_icon = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            # Tampilkan gambar jika ada di dalam riwayat pesan
            if "image" in msg and msg["image"]:
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])

# -----------------------------------------------------------------------------
# 6. INPUT USER & PROSES AI
# -----------------------------------------------------------------------------
prompt_data = st.chat_input(
    "ketik keluhan kerusakan...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
    key="chat_input_main"
)

if prompt_data:
    raw_prompt = prompt_data.text
    uploaded_files = prompt_data.files

    # A. Sanitasi teks
    clean_prompt = raw_prompt.encode("ascii", errors="ignore").decode("ascii")
    clean_prompt = re.sub(r'[\u200b-\u200d\ufeff\u200e\u200f]', '', clean_prompt).strip()

    if clean_prompt or uploaded_files:
        display_text = clean_prompt if clean_prompt else "[Mengirim Gambar]"
        image_bytes_data = None
        image_type = None

        # B. Olah gambar jika user mengunggah foto
        if uploaded_files:
            uploaded_image = uploaded_files[0]
            image_bytes_data = uploaded_image.getvalue()
            image_type = uploaded_image.type

        # C. Tampilkan pesan user di UI secara langsung
        with st.chat_message("user", avatar="👤"):
            if image_bytes_data:
                st.image(image_bytes_data, use_container_width=True)
            st.markdown(display_text)

        # D. Simpan ke session state (Teks + Gambar)
        st.session_state.messages.append({
            "role": "user",
            "content": display_text,
            "image": image_bytes_data,
            "image_type": image_type
        })

        # E. Kirim ke AI & Tampilkan Jawaban
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Menganalisis pertanyaan dan gambar..."):
                try:
                    messages_for_api = []
                    total_messages = len(st.session_state.messages)
                    
                    for idx, msg in enumerate(st.session_state.messages):
                        if msg["role"] == "system":
                            messages_for_api.append({"role": "system", "content": msg["content"]})
                        elif msg["role"] == "assistant":
                            messages_for_api.append({"role": "assistant", "content": msg["content"]})
                        elif msg["role"] == "user":
                            if msg.get("image") and (total_messages - idx <= 6):
                                image_base64 = base64.b64encode(msg["image"]).decode("utf-8")
                                messages_for_api.append({
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": msg["content"]},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{msg['image_type']};base64,{image_base64}"
                                            }
                                        }
                                    ]
                                })
                            else:
                                messages_for_api.append({"role": "user", "content": msg["content"]})

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages_for_api
                    )

                    jawaban = response.choices[0].message.content
                    st.markdown(jawaban)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": jawaban
                    })

                except Exception as e:
                    st.error(f"Terjadi kesalahan pada sistem: {e}")
