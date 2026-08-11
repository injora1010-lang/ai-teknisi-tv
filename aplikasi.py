import re
import os
import base64
import uuid
import streamlit as st
from openai import OpenAI
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Service TV Pro - Asisten Teknisi",
    page_icon="📺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Style CSS Kustom & Footer
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .block-container { padding-bottom: 90px; }
    
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
    .custom-footer b { color: #ffffff; }
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
# 2. INISIALISASI OPENAI & SUPABASE
# -----------------------------------------------------------------------------
api_key = st.secrets["OPENAI_API_KEY"].encode("ascii", errors="ignore").decode("ascii").strip()
client = OpenAI(api_key=api_key)

supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

SYSTEM_PROMPT = """
Kamu adalah AI Asisten Senior Teknisi Elektronik dan Service TV Profesional.
Tugas utama kamu adalah membantu teknisi memahami, menganalisis, dan memperbaiki
TV LED, LCD, OLED, Plasma, TV Tabung, power supply, mainboard, T-Con,
backlight, panel, serta rangkaian elektronik lainnya.

ATURAN UTAMA:
1. PAHAMI PERTANYAAN TERLEBIH DAHULU.
2. JAWAB SESUAI JENIS PERTANYAAN DAN FLEKSIBEL.
3. GUNAKAN BAHASA INDONESIA YANG MUDAH DIPAHAMI TEKNISI BENGKEL.
4. PERHATIKAN KESELAMATAN (TEGANGAN TINGGI).
"""

# Manajemen Session ID (Kunci riwayat pengguna)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Muat riwayat chat dari Supabase jika session_state masih kosong
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    try:
        response = supabase.table("chat_history")\
            .select("*")\
            .eq("session_id", st.session_state.session_id)\
            .order("created_at", desc=False)\
            .execute()
        
        for record in response.data:
            msg_obj = {"role": record["role"], "content": record["content"]}
            if record.get("image_url"):
                # Decode string base64 kembali ke bytes
                msg_obj["image"] = base64.b64decode(record["image_url"])
            st.session_state.messages.append(msg_obj)
    except Exception as e:
        pass

# -----------------------------------------------------------------------------
# 3. SIDEBAR PENGATURAN
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    st.write("Pengembang: **Rasmuhammad**")
    st.write("Status Sistem: 🟢 **Aktif (Supabase Linked)**")
    st.markdown("---")
    
    if st.button("🗑️ Reset Sesi Diagnosa", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

# -----------------------------------------------------------------------------
# 4. MERENDER RIWAYAT CHAT
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        avatar_icon = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            if "image" in msg and msg["image"]:
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])

# -----------------------------------------------------------------------------
# 5. INPUT USER & PROSES AI
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

    clean_prompt = raw_prompt.encode("ascii", errors="ignore").decode("ascii")
    clean_prompt = re.sub(r'[\u200b-\u200d\ufeff\u200e\u200f]', '', clean_prompt).strip()

    if clean_prompt or uploaded_files:
        display_text = clean_prompt if clean_prompt else "[Mengirim Gambar]"
        image_bytes_data = None
        image_type = None
        image_b64_str = None

        if uploaded_files:
            uploaded_image = uploaded_files[0]
            image_bytes_data = uploaded_image.getvalue()
            image_type = uploaded_image.type
            image_b64_str = base64.b64encode(image_bytes_data).decode("utf-8")

        # Tampilkan di UI
        with st.chat_message("user", avatar="👤"):
            if image_bytes_data:
                st.image(image_bytes_data, use_container_width=True)
            st.markdown(display_text)

        # Simpan ke session_state
        st.session_state.messages.append({
            "role": "user",
            "content": display_text,
            "image": image_bytes_data,
            "image_type": image_type
        })

        # Simpan pesan User ke Supabase
        try:
            supabase.table("chat_history").insert({
                "session_id": st.session_state.session_id,
                "role": "user",
                "content": display_text,
                "image_url": image_b64_str
            }).execute()
        except Exception:
            pass

        # Respon AI
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Menganalisis..."):
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

                    # Simpan balasan AI ke Supabase
                    supabase.table("chat_history").insert({
                        "session_id": st.session_state.session_id,
                        "role": "assistant",
                        "content": jawaban
                    }).execute()

                except Exception as e:
                    st.error(f"Terjadi kesalahan pada sistem: {e}")
