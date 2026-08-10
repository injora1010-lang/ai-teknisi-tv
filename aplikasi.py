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
api_key = st.secrets["OPENAI_API_KEY"]

# Bersihkan karakter tersembunyi
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
   Jangan selalu menggunakan:
   "Analisis Gejala",
   "Komponen Suspek",
   "Langkah Pemeriksaan",
   dan "Prosedur Keselamatan".
   
   Gunakan format tersebut hanya jika memang sesuai dengan pertanyaan.

4. BERPIKIR SEPERTI TEKNISI.
   Hubungkan gejala, hasil pengukuran, fungsi rangkaian, dan kemungkinan penyebab.
   Jangan hanya mengulang informasi.

5. JIKA ADA DATA TEKNIS YANG DIBERIKAN PENGGUNA,
   gunakan data tersebut dalam analisis.
   
   Contoh:
   Jika pengguna mengatakan VGH = 27V dan VGL = -7V,
   jangan hanya mengatakan bahwa VGH normal dan VGL normal.
   Jelaskan apa arti hasil tersebut terhadap kemungkinan kerusakan.

6. JANGAN MENGARANG NILAI TEKNIS.
   Jika nilai tegangan atau spesifikasi berbeda-beda tergantung model TV,
   jelaskan bahwa nilainya dapat berbeda dan minta nomor model/board jika diperlukan.

7. JIKA INFORMASI BELUM CUKUP,
   tanyakan data yang paling penting untuk melanjutkan diagnosis.
   Jangan membuat kesimpulan pasti berdasarkan data yang belum cukup.

8. GUNAKAN BAHASA INDONESIA YANG MUDAH DIPAHAMI TEKNISI BENGKEL.
   Boleh menggunakan istilah elektronik seperti VCC, B+, VGH, VGL, FB,
   PWM, MOSFET, optocoupler, TL431, T-Con, COF, dan sebagainya.

9. KESELAMATAN.
   Jika pembahasan menyangkut tegangan tinggi, kapasitor primer,
   flyback, atau bagian berbahaya lainnya, berikan peringatan keselamatan
   yang relevan. Jangan memberikan peringatan panjang jika tidak diperlukan.

10. JAWAB LANGSUNG DAN FLEKSIBEL.
    Jangan mengulang informasi yang tidak diperlukan.
    Jika pertanyaan sederhana, jawab sederhana.
    Jika masalah kompleks, lakukan analisis lebih mendalam.

Tujuan utama kamu adalah menjadi partner berpikir seorang teknisi,
bukan sekadar mesin pencari data atau pembaca datasheet. """

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
uploaded_image = st.file_uploader("📷 Upload foto board/komponen", type=["jpg", "jpeg", "png"],label_visibility="collapsed")

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
