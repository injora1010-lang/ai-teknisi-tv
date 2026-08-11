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
    page_title="AI Service TV Pro",
    page_icon="📺",
    layout="centered"
)

# -----------------------------------------------------------------------------
# 2. AUTENTIKASI STREAMLIT USER
# -----------------------------------------------------------------------------
# Penanganan aman untuk versi Streamlit baru maupun lama
user_data = getattr(st, "user", None) or getattr(st, "experimental_user", None)

if not user_data or not getattr(user_data, "is_logged_in", False):
    st.title("📺 AI Service TV Pro")
    st.subheader("Silakan Login Terlebih Dahulu")
    st.write("Login menggunakan akun Google untuk mengakses aplikasi dan menyimpan riwayat perbaikan Anda.")
    
    if st.button("🔑 Login dengan Google", type="primary"):
        st.login("google") if hasattr(st, "login") else st.login()
    st.stop()

# Ambil informasi pengguna dari sesi login
user_email = user_data.email
user_name = getattr(user_data, "name", user_email.split("@")[0])

# -----------------------------------------------------------------------------
# 3. KONEKSI SUPABASE & OPENAI
# -----------------------------------------------------------------------------
api_key = st.secrets["OPENAI_API_KEY"].strip()
client = OpenAI(api_key=api_key)

supabase_url = st.secrets["SUPABASE_URL"].strip()
supabase_key = st.secrets["SUPABASE_KEY"].strip()
supabase: Client = create_client(supabase_url, supabase_key)

SYSTEM_PROMPT = (
    "Kamu adalah AI Asisten Senior Service TV Profesional. "
    "Bantu pengguna mendiagnosa kerusakan TV LED, LCD, OLED, Plasma, dan TV Tabung dengan cermat dan solutif."
)

# -----------------------------------------------------------------------------
# 4. MEMUAT RIWAYAT CHAT KHUSUS USER INI DARI SUPABASE
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    try:
        response = (
            supabase.table("chat_history")
            .select("*")
            .eq("user_email", user_email)
            .order("created_at", desc=False)
            .execute()
        )
        for record in response.data:
            st.session_state.messages.append({
                "role": record["role"],
                "content": record["content"]
            })
    except Exception as e:
        pass

# -----------------------------------------------------------------------------
# 5. HEADER & SIDEBAR BARU
# -----------------------------------------------------------------------------
st.title("📺 AI SERVICE TV PRO")
st.caption(f"Selamat datang, **{user_name}** (`{user_email}`)")

with st.sidebar:
    st.header("👤 Profil Pengguna")
    st.write(f"**Nama:** {user_name}")
    st.write(f"**Email:** {user_email}")
    st.markdown("---")
    if st.button("🚪 Logout", type="secondary"):
        st.logout()

# -----------------------------------------------------------------------------
# 6. ENGINE CHAT & PENYIMPANAN DATA SIKLUS REALTIME
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

prompt = st.chat_input("Ketik keluhan kerusakan TV...")

if prompt:
    st.chat_message("user", avatar="👤").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Simpan Pertanyaan Pengguna ke Supabase
    try:
        supabase.table("chat_history").insert({
            "session_id": user_email,
            "user_email": user_email,
            "role": "user",
            "content": prompt
        }).execute()
    except Exception:
        pass

    # Kirim Pertanyaan ke OpenAI API
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Menganalisis jenis kerusakan TV..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                jawaban = response.choices[0].message.content
                st.markdown(jawaban)

                st.session_state.messages.append({"role": "assistant", "content": jawaban})

                # Simpan Respon AI ke Supabase
                supabase.table("chat_history").insert({
                    "session_id": user_email,
                    "user_email": user_email,
                    "role": "assistant",
                    "content": jawaban
                }).execute()
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses respon AI: {e}")
