import streamlit as st
from openai import OpenAI
from supabase import create_client, Client
from uuid import uuid4


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

raw_key = st.secrets["OPENAI_API_KEY"].strip()

api_key = (
    raw_key
    .encode("ascii", "ignore")
    .decode("ascii")
)

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
    "serta langkah perbaikan berdasarkan gejala yang diberikan. "
    "Jika informasi belum cukup, tanyakan data pemeriksaan yang diperlukan."
)


# =============================================================================
# 5. STATUS LOGIN
# =============================================================================

try:

    is_logged_in = st.user.is_logged_in

except Exception:

    is_logged_in = False


if is_logged_in:

    user_email = getattr(
        st.user,
        "email",
        None
    )

    user_name = getattr(
        st.user,
        "name",
        user_email.split("@")[0]
        if user_email
        else "Pengguna"
    )

else:

    user_email = None
    user_name = "Pengguna"


# =============================================================================
# 6. FUNGSI SESSION
# =============================================================================

def create_new_session():

    return str(uuid4())


def empty_messages():

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


def load_chat_session(session_id):

    messages = empty_messages()

    if not is_logged_in or not user_email:
        return messages

    try:

        response = (
            supabase
            .table("chat_history")
            .select("role, content, created_at")
            .eq("user_email", user_email)
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )

        for record in response.data:

            if record["role"] in ["user", "assistant"]:

                messages.append({
                    "role": record["role"],
                    "content": record["content"]
                })

    except Exception as e:

        st.warning(
            f"Tidak dapat memuat riwayat chat: {e}"
        )

    return messages


def get_chat_sessions():

    sessions = []

    if not is_logged_in or not user_email:
        return sessions

    try:

        response = (
            supabase
            .table("chat_history")
            .select("session_id, role, content, created_at")
            .eq("user_email", user_email)
            .order("created_at", desc=True)
            .execute()
        )

        session_data = {}

        for record in response.data:

            session_id = record.get("session_id")

            if not session_id:
                continue

            if session_id not in session_data:

                session_data[session_id] = {
                    "session_id": session_id,
                    "title": "Chat Baru",
                    "created_at": record.get("created_at")
                }

            # Ambil pertanyaan pertama sebagai judul chat
            if (
                record.get("role") == "user"
                and session_data[session_id]["title"] == "Chat Baru"
            ):

                title = record.get("content", "").strip()

                if title:

                    title = title.replace("\n", " ")

                    if len(title) > 35:
                        title = title[:35] + "..."

                    session_data[session_id]["title"] = title

        sessions = list(session_data.values())

        # Sudah urut berdasarkan data terbaru,
        # tetapi kita batasi maksimal 5 sesi.
        sessions = sessions[:5]

    except Exception:

        pass

    return sessions


def save_message(session_id, role, content):

    if not is_logged_in or not user_email:
        return

    try:

        supabase.table("chat_history").insert({

            "session_id": session_id,

            "user_email": user_email,

            "role": role,

            "content": content

        }).execute()

    except Exception:

        pass


# =============================================================================
# 7. SESSION STATE
# =============================================================================

if "active_session_id" not in st.session_state:

    st.session_state.active_session_id = None


if "messages" not in st.session_state:

    st.session_state.messages = empty_messages()


# =============================================================================
# 8. INISIALISASI SESSION SAAT LOGIN
# =============================================================================

if is_logged_in and user_email:

    if st.session_state.active_session_id is None:

        sessions = get_chat_sessions()

        if sessions:

            # Buka chat terakhir
            st.session_state.active_session_id = (
                sessions[0]["session_id"]
            )

            st.session_state.messages = load_chat_session(
                st.session_state.active_session_id
            )

        else:

            # Belum ada chat
            st.session_state.active_session_id = create_new_session()

            st.session_state.messages = empty_messages()


else:

    # Mode tamu
    if st.session_state.active_session_id is None:

        st.session_state.active_session_id = create_new_session()

        st.session_state.messages = empty_messages()


# =============================================================================
# 9. SIDEBAR
# =============================================================================

with st.sidebar:

    st.header("📺 AI Service TV Pro")

    st.caption("Asisten AI Teknisi Service TV")

    st.markdown("---")


    # -------------------------------------------------------------------------
    # LOGIN
    # -------------------------------------------------------------------------

    if is_logged_in:

        st.success("🟢 Login aktif")

        st.write(f"**Nama:** {user_name}")

        st.write(f"**Email:** {user_email}")

        st.markdown("---")

    else:

        st.info(
            "💬 Mode tamu"
        )

        st.write(
            "Login diperlukan untuk menyimpan "
            "dan membuka kembali riwayat chat."
        )

        if st.button(
            "🔑 Login dengan Google",
            type="primary",
            use_container_width=True
        ):

            st.login("google")

        st.markdown("---")


    # -------------------------------------------------------------------------
    # CHAT BARU
    # -------------------------------------------------------------------------

    if st.button(
        "🆕 Chat Baru",
        use_container_width=True
    ):

        st.session_state.active_session_id = (
            create_new_session()
        )

        st.session_state.messages = empty_messages()

        st.rerun()


    st.markdown("---")


    # -------------------------------------------------------------------------
    # RIWAYAT CHAT
    # -------------------------------------------------------------------------

    if is_logged_in:

        st.subheader("💬 Riwayat Chat")

        sessions = get_chat_sessions()

        if sessions:

            for index, chat in enumerate(sessions):

                session_id = chat["session_id"]

                title = chat["title"]

                # Tandai chat yang sedang aktif
                if (
                    session_id
                    == st.session_state.active_session_id
                ):

                    label = f"🔵 {title}"

                else:

                    label = f"💬 {title}"


                if st.button(
                    label,
                    key=f"chat_session_{session_id}",
                    use_container_width=True
                ):

                    st.session_state.active_session_id = (
                        session_id
                    )

                    st.session_state.messages = (
                        load_chat_session(session_id)
                    )

                    st.rerun()

        else:

            st.caption(
                "Belum ada riwayat chat."
            )


    # -------------------------------------------------------------------------
    # PENGEMBANG
    # -------------------------------------------------------------------------

    st.markdown("---")

    st.caption("**Pengembang:** Rasmuhammad")


    # -------------------------------------------------------------------------
    # LOGOUT
    # -------------------------------------------------------------------------

    if is_logged_in:

        st.markdown("---")

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.logout()


# =============================================================================
# 10. HEADER UTAMA
# =============================================================================

st.title("📺 AI SERVICE TV PRO")


if is_logged_in:

    st.caption(
        f"Selamat datang, **{user_name}**"
    )

    st.success(
        "🔐 Login aktif — riwayat chat tersimpan di server."
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
# 11. TAMPILKAN CHAT
# =============================================================================

for msg in st.session_state.messages:

    if msg["role"] == "system":
        continue


    if msg["role"] == "user":

        with st.chat_message(
            "user",
            avatar="👤"
        ):

            st.markdown(
                msg["content"]
            )


    elif msg["role"] == "assistant":

        with st.chat_message(
            "assistant",
            avatar="🤖"
        ):

            st.markdown(
                msg["content"]
            )


# =============================================================================
# 12. INPUT CHAT
# =============================================================================

prompt = st.chat_input(
    "Ketik keluhan kerusakan TV..."
)


# =============================================================================
# 13. PROSES CHAT
# =============================================================================

if prompt:

    # -------------------------------------------------------------------------
    # TAMPILKAN PESAN USER
    # -------------------------------------------------------------------------

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        st.markdown(prompt)


    # -------------------------------------------------------------------------
    # SIMPAN KE SESSION STATE
    # -------------------------------------------------------------------------

    st.session_state.messages.append({

        "role": "user",

        "content": prompt

    })


    # -------------------------------------------------------------------------
    # SIMPAN KE SUPABASE
    # -------------------------------------------------------------------------

    save_message(
        st.session_state.active_session_id,
        "user",
        prompt
    )


    # -------------------------------------------------------------------------
    # KIRIM KE OPENAI
    # -------------------------------------------------------------------------

    with st.chat_message(
        "assistant",
        avatar="🤖"
    ):

        with st.spinner(
            "🔧 Menganalisis kerusakan TV..."
        ):

            try:

                # Ambil maksimal 20 pesan terakhir
                # + system prompt
                recent_messages = (
                    st.session_state.messages[-20:]
                )


                messages_for_ai = [

                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }

                ] + [

                    {
                        "role": m["role"],
                        "content": (
                            m["content"]
                            .encode(
                                "utf-8",
                                "ignore"
                            )
                            .decode("utf-8")
                        )
                    }

                    for m in recent_messages
                    if m["role"] in ["user", "assistant"]

                ]


                response = client.chat.completions.create(

                    model="gpt-4o-mini",

                    messages=messages_for_ai

                )


                jawaban = (
                    response
                    .choices[0]
                    .message
                    .content
                )


                # -----------------------------------------------------------------
                # TAMPILKAN JAWABAN AI
                # -----------------------------------------------------------------

                st.markdown(
                    jawaban
                )


                # -----------------------------------------------------------------
                # SIMPAN JAWABAN KE SESSION STATE
                # -----------------------------------------------------------------

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": jawaban

                })


                # -----------------------------------------------------------------
                # SIMPAN JAWABAN AI KE SUPABASE
                # -----------------------------------------------------------------

                save_message(
                    st.session_state.active_session_id,
                    "assistant",
                    jawaban
                )


            except Exception as e:

                st.error(
                    f"Terjadi kesalahan saat memproses AI: {e}"
                )


# =============================================================================
# 14. FOOTER / COPYRIGHT
# =============================================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#888;
        font-size:13px;
        margin-top:40px;
        padding:15px 0;
        border-top:1px solid rgba(128,128,128,0.2);
    ">
        <b>AI TEKNISI & SERVICE TV PRO</b><br>
        Sistem Pakar Diagnosa Kerusakan TV LED, LCD, OLED, Plasma, & TV Tabung<br>
        © 2026 Rasmuhammad
    </div>
    """,
    unsafe_allow_html=True
)