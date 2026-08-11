import streamlit as st
from openai import OpenAI
from supabase import create_client, Client

# =============================================================================
# 1. KONFIGURASI HALAMAN
# =============================================================================

st.set_page_config(
    page_title="AI Service TV Pro",
    page_icon="📺",
    layout="centered"
)

# =============================================================================
# 2. OPENAI
# =============================================================================

api_key = st.secrets["OPENAI_API_KEY"].strip()
client = OpenAI(api_key=api_key)

# =============================================================================
# 3. SUPABASE
# =============================================================================

supabase_url = st.secrets["SUPABASE_URL"].strip()
supabase_key = st.secrets["SUPABASE_KEY"].strip()

supabase: Client = create_client(
    supabase_url,
    supabase_key
)

# =============================================================================
# 4. SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = (
    "Kamu adalah AI Asisten Senior Service TV Profesional. "
    "Bantu pengguna mendiagnosa kerusakan TV LED, LCD, OLED, Plasma, "
    "dan TV Tabung dengan cermat, sistematis, aman, dan solutif. "
    "Berikan langkah pemeriksaan menggunakan multitester, "
    "tegangan penting, kemungkinan kerusakan komponen, "
    "serta langkah perbaikan berdasarkan gejala yang diberikan."
)

# =============================================================================
# 5. STATUS LOGIN
# =============================================================================

try:
    is_logged_in = st.user.is_logged_in
except Exception:
    is_logged_in = False


if is_logged_in:

    user_email = getattr(st.user, "email", None)

    user_name = getattr(
        st.user,
        "name",
        user_email.split("@")[0] if user_email else "Pengguna"
    )

else:

    user_email = None
    user_name = "Pengguna"


# =============================================================================
# 6. SESSION STATE
# =============================================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Kalau login → ambil riwayat dari Supabase
    if is_logged_in and user_email:

        try:

            response = (
                supabase
                .table("chat_history")
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

        except Exception:

            st.warning(
                "Tidak dapat memuat riwayat chat dari server."
            )


# =============================================================================
# 7. SIDEBAR
# =============================================================================

with st.sidebar:

    st.header("📺 AI Service TV Pro")

    st.markdown("---")

    if is_logged_in:

        st.success("🟢 Login")

        st.write(f"**Nama:** {user_name}")
        st.write(f"**Email:** {user_email}")

        st.markdown("---")

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):
            st.logout()

    else:

        st.info(
            "💬 Anda dapat menggunakan AI tanpa login."
        )

        st.write(
            "Login diperlukan jika Anda ingin "
            "menyimpan riwayat chat."
        )

        if st.button(
            "🔑 Login dengan Google",
            type="primary",
            use_container_width=True
        ):
            st.login("google")

    st.markdown("---")

    if st.button(
        "🆕 Chat Baru",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        st.rerun()


# =============================================================================
# 8. HEADER
# =============================================================================

st.title("📺 AI SERVICE TV PRO")

if is_logged_in:

    st.caption(
        f"Selamat datang, **{user_name}**"
    )

    st.success(
        "🔐 Login aktif — riwayat chat akan disimpan."
    )

else:

    st.caption(
        "Asisten AI untuk teknisi service TV"
    )

    st.info(
        "💬 Mode tamu — Anda bisa chat tanpa login. "
        "Riwayat tidak disimpan ke database."
    )


# =============================================================================
# 9. TAMPILKAN CHAT
# =============================================================================

for msg in st.session_state.messages:

    if msg["role"] == "system":
        continue

    if msg["role"] == "user":

        with st.chat_message(
            "user",
            avatar="👤"
        ):
            st.markdown(msg["content"])

    elif msg["role"] == "assistant":

        with st.chat_message(
            "assistant",
            avatar="🤖"
        ):
            st.markdown(msg["content"])


# =============================================================================
# 10. INPUT CHAT
# =============================================================================

prompt = st.chat_input(
    "Ketik keluhan kerusakan TV..."
)


# =============================================================================
# 11. PROSES CHAT
# =============================================================================

if prompt:

    # Tampilkan pertanyaan user

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        st.markdown(prompt)

    # Simpan ke session

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })


    # =========================================================================
    # SIMPAN PERTANYAAN KE SUPABASE
    # HANYA JIKA LOGIN
    # =========================================================================

    if is_logged_in and user_email:

        try:

            supabase.table("chat_history").insert({

                "session_id": user_email,

                "user_email": user_email,

                "role": "user",

                "content": prompt

            }).execute()

        except Exception:

            pass


    # =========================================================================
    # KIRIM KE OPENAI
    # =========================================================================

    with st.chat_message(
        "assistant",
        avatar="🤖"
    ):

        with st.spinner(
            "🔧 Menganalisis kerusakan TV..."
        ):

            try:

                response = client.chat.completions.create(

                    model="gpt-4o-mini",

                    messages=[
                        {
                            "role": m["role"],
                            "content": m["content"]
                        }

                        for m in st.session_state.messages
                    ]
                )

                jawaban = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                st.markdown(jawaban)


                # Simpan jawaban AI ke session

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": jawaban
                })


                # =========================================================================
                # SIMPAN JAWABAN AI KE SUPABASE
                # HANYA JIKA LOGIN
                # =========================================================================

                if is_logged_in and user_email:

                    try:

                        supabase.table(
                            "chat_history"
                        ).insert({

                            "session_id": user_email,

                            "user_email": user_email,

                            "role": "assistant",

                            "content": jawaban

                        }).execute()

                    except Exception:

                        pass


            except Exception as e:

                st.error(
                    f"Terjadi kesalahan saat memproses AI: {e}"
                )