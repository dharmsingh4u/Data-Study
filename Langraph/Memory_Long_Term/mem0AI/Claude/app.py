"""Streamlit UI for the AI Interview Prep Coach — production layout."""

import json
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from memory_agent import (
    AgentError,
    MAX_MESSAGE_LEN,
    MAX_USER_ID_LEN,
    GEMINI_CHAT_MODEL,
    GEMINI_EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    MEMORY_SEARCH_LIMIT,
    SetupError,
    ValidationError,
    chat,
    get_all_memories,
    health_check,
)

# ---------------------------------------------------------------------------
# Page config  (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Interview Prep Coach",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background-color: #0f1117; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d2e 0%, #12151f 100%);
        border-right: 1px solid #2a2d3e;
    }
    [data-testid="stSidebar"] * { color: #c9d1e0 !important; }

    /* Tabs */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid #2a2d3e;
        gap: 4px;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background: transparent !important;
        color: #4b5563 !important;
        font-size: 0.88rem;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        border-radius: 8px 8px 0 0;
        border: 1px solid transparent !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: #1a1d2e !important;
        color: #93c5fd !important;
        border-color: #2a2d3e !important;
        border-bottom-color: #1a1d2e !important;
    }

    /* Hero */
    .hero {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 60%, #1a1d2e 100%);
        border: 1px solid #2a4a6e;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
    }
    .hero h1 { font-size: 2rem; font-weight: 700; color: #e8f4fd !important; margin: 0 0 0.4rem 0; }
    .hero p  { color: #7eb3d4 !important; font-size: 0.95rem; margin: 0; }

    /* Status pills */
    .status-pill { display:inline-flex; align-items:center; gap:6px; padding:4px 12px;
                   border-radius:20px; font-size:0.78rem; font-weight:600; }
    .status-online  { background:#0d2e1a; color:#4ade80; border:1px solid #166534; }
    .status-offline { background:#2e0d0d; color:#f87171; border:1px solid #991b1b; }

    /* Metric cards */
    .metric-row { display:flex; gap:12px; margin-bottom:1.2rem; }
    .metric-card { flex:1; background:#1a1d2e; border:1px solid #2a2d3e; border-radius:12px;
                   padding:1rem 1.2rem; text-align:center; }
    .metric-card .metric-value { font-size:1.8rem; font-weight:700; color:#60a5fa; line-height:1; }
    .metric-card .metric-label { font-size:0.72rem; color:#6b7280; text-transform:uppercase;
                                 letter-spacing:0.06em; margin-top:4px; }

    /* Memory chip */
    .memory-chip { background:#1a1d2e; border:1px solid #2a2d3e; border-left:3px solid #3b82f6;
                   border-radius:6px; padding:0.45rem 0.75rem; font-size:0.82rem;
                   color:#c9d1e0; margin-bottom:6px; line-height:1.4; }

    /* Sidebar section headers */
    .sidebar-section { font-size:0.7rem; font-weight:700; letter-spacing:0.1em;
                       text-transform:uppercase; color:#4b5563 !important;
                       margin:1.2rem 0 0.5rem 0; }

    /* Buttons */
    .stButton > button { width:100%; background:#1e3a5f; color:#93c5fd !important;
                         border:1px solid #2a4a6e; border-radius:8px; font-size:0.85rem;
                         font-weight:500; padding:0.45rem 1rem; transition:all 0.2s; }
    .stButton > button:hover { background:#2a4a7a; border-color:#3b82f6; color:#bfdbfe !important; }
    .stButton > button:disabled { opacity:0.35 !important; }
    .stDownloadButton > button { width:100%; background:transparent !important;
                                  color:#6b7280 !important; border:1px dashed #374151 !important;
                                  border-radius:8px; font-size:0.82rem; }

    /* Chat input */
    [data-testid="stChatInput"] textarea {
        background:#1a1d2e !important; border:1px solid #2a4a6e !important;
        border-radius:12px !important; color:#e8f4fd !important; font-size:0.92rem; }
    [data-testid="stChatInput"] textarea:focus {
        border-color:#3b82f6 !important;
        box-shadow:0 0 0 3px rgba(59,130,246,0.15) !important; }

    /* Text inputs */
    [data-testid="stTextInput"] input {
        background:#1a1d2e !important; border:1px solid #2a2d3e !important;
        border-radius:8px !important; color:#e8f4fd !important; font-size:0.88rem; }
    [data-testid="stTextInput"] input:focus { border-color:#3b82f6 !important; }
    [data-testid="stTextInput"] label {
        font-size:0.78rem !important; font-weight:600 !important;
        letter-spacing:0.04em !important; text-transform:uppercase !important;
        color:#6b7280 !important; }

    hr { border-color:#1f2937 !important; }
    [data-testid="stAlert"] { border-radius:10px; font-size:0.88rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_memories" not in st.session_state:
    st.session_state.show_memories = False

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_USER_ID_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

with st.sidebar:
    st.markdown(
        "<div style='padding:1rem 0 0.5rem;'>"
        "<span style='font-size:1.5rem;'>🧠</span>"
        "<span style='font-size:1.1rem;font-weight:700;color:#e8f4fd;margin-left:8px;'>"
        "Prep Coach</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-section'>Identity</div>", unsafe_allow_html=True)
    user_id: str = st.text_input(
        "User ID",
        value="alice",
        max_chars=MAX_USER_ID_LEN,
        help="Alphanumeric + _ - . only. Memories are namespaced to this ID.",
    )
    _user_id_ok = bool(user_id.strip()) and bool(_USER_ID_RE.match(user_id))
    if user_id and not _user_id_ok:
        st.warning("Only letters, digits, _, -, and . are allowed.")

    st.markdown("<div class='sidebar-section'>System</div>", unsafe_allow_html=True)
    _health = health_check()
    _backend_ok = _health["status"] == "healthy"
    if _backend_ok:
        st.markdown("<span class='status-pill status-online'>● Memory online</span>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<span class='status-pill status-offline'>● Memory offline</span>",
                    unsafe_allow_html=True)
        st.caption(_health["detail"])

    msg_count = len(st.session_state.messages)
    user_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
    st.markdown(
        f"""<div class='metric-row' style='margin-top:1rem;'>
            <div class='metric-card'>
                <div class='metric-value'>{msg_count}</div>
                <div class='metric-label'>Messages</div>
            </div>
            <div class='metric-card'>
                <div class='metric-value'>{user_turns}</div>
                <div class='metric-label'>Your turns</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-section'>Long-term memory</div>", unsafe_allow_html=True)
    if st.button("Load memories", disabled=not _user_id_ok):
        st.session_state.show_memories = True

    if st.session_state.show_memories and _user_id_ok:
        with st.spinner("Fetching..."):
            _mem_result = get_all_memories(user_id)
        _mem_items = _mem_result.get("results", [])
        if "error" in _mem_result:
            st.error(_mem_result["error"])
        elif not _mem_items:
            st.info("Nothing stored yet.")
        else:
            st.caption(f"{len(_mem_items)} memor{'y' if len(_mem_items) == 1 else 'ies'}")
            for item in _mem_items:
                text = item.get("memory", "")
                if text:
                    st.markdown(f"<div class='memory-chip'>{text}</div>",
                                unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section'>Actions</div>", unsafe_allow_html=True)
    if st.session_state.messages:
        _export = json.dumps(
            {"user_id": user_id, "exported_at": datetime.now().isoformat(),
             "messages": st.session_state.messages},
            indent=2,
        )
        st.download_button(
            label="⬇ Export chat (JSON)",
            data=_export,
            file_name=f"chat_{user_id}_{datetime.now():%Y%m%d_%H%M%S}.json",
            mime="application/json",
        )
    if st.button("Clear transcript", disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.session_state.show_memories = False
        st.rerun()

    st.markdown(
        "<div style='position:absolute;bottom:1rem;left:1rem;right:1rem;"
        "font-size:0.7rem;color:#374151;text-align:center;'>"
        "Powered by Gemini · Mem0 · LangChain</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_chat, tab_arch = st.tabs(["💬  Chat", "🏗  Architecture"])

# ============================================================
#  TAB 1 — Chat
# ============================================================

with tab_chat:
    _col_chat, _col_info = st.columns([3, 1], gap="large")

    with _col_info:
        st.markdown(
            """<div style='background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;
                          padding:1.2rem;margin-top:0.5rem;'>
                <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;color:#4b5563;margin-bottom:0.8rem;'>
                    Tips
                </div>
                <div style='font-size:0.82rem;color:#6b7280;line-height:1.7;'>
                    💡 Tell the coach your <b style='color:#93c5fd;'>target role</b><br>
                    📚 Share topics you've <b style='color:#93c5fd;'>studied</b><br>
                    🎯 Mention your <b style='color:#93c5fd;'>weak areas</b><br>
                    🔄 Memories persist across <b style='color:#93c5fd;'>sessions</b>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """<div style='background:#13161f;border:1px solid #1f2937;border-radius:10px;
                          padding:1rem;margin-top:0.8rem;'>
                <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;color:#374151;margin-bottom:0.6rem;'>
                    Shortcuts
                </div>
                <div style='font-size:0.78rem;color:#4b5563;line-height:1.8;'>
                    <kbd style='background:#1f2937;border:1px solid #374151;border-radius:4px;
                                padding:1px 6px;color:#6b7280;'>Enter</kbd> Send<br>
                    <kbd style='background:#1f2937;border:1px solid #374151;border-radius:4px;
                                padding:1px 6px;color:#6b7280;'>Shift+Enter</kbd> New line
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with _col_chat:
        st.markdown(
            f"""<div class='hero'>
                <h1>AI Interview Prep Coach</h1>
                <p>Personalised coaching that remembers your progress across every session.
                &nbsp;·&nbsp; Signed in as
                <strong style='color:#93c5fd;'>{user_id or "—"}</strong></p>
            </div>""",
            unsafe_allow_html=True,
        )

        _chat_disabled = not _user_id_ok or not _backend_ok
        if not _backend_ok:
            st.error("Memory backend is offline — check your API keys and restart.")
        elif not _user_id_ok:
            st.warning("Enter a valid User ID in the sidebar to start chatting.")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if not st.session_state.messages and not _chat_disabled:
            st.markdown(
                """<div style='text-align:center;padding:3rem 1rem;'>
                    <div style='font-size:2.5rem;margin-bottom:0.8rem;'>👋</div>
                    <div style='font-size:1rem;color:#4b5563;'>
                        Start by telling the coach your target role<br>
                        or ask for your first question.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        if prompt := st.chat_input(
            "Tell me about your prep, or answer my question…",
            disabled=_chat_disabled,
        ):
            if len(prompt) > MAX_MESSAGE_LEN:
                st.error(f"Message too long — keep it under {MAX_MESSAGE_LEN:,} characters.")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        try:
                            reply = chat(user_id=user_id, user_message=prompt)
                            st.markdown(reply)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": reply}
                            )
                        except ValidationError as exc:
                            st.error(f"Invalid input: {exc}")
                        except SetupError as exc:
                            st.error(f"Backend error — check your configuration: {exc}")
                        except AgentError as exc:
                            st.error(f"Something went wrong, please try again: {exc}")

# ============================================================
#  TAB 2 — Architecture
# ============================================================

with tab_arch:

    st.markdown(
        f"""<div class='hero' style='margin-bottom:1rem;'>
            <h1 style='font-size:1.5rem;'>Message Flow & Memory Architecture</h1>
            <p>How each user turn is processed — from input to Mem0 long-term storage and back.</p>
            <p style='margin-top:0.6rem;font-size:0.8rem;color:#4b7a9c;'>
                LLM&nbsp;<strong style='color:#60a5fa;'>{GEMINI_CHAT_MODEL}</strong>
                &nbsp;·&nbsp;
                Embedder&nbsp;<strong style='color:#60a5fa;'>{GEMINI_EMBEDDING_MODEL}</strong>
                &nbsp;·&nbsp;
                Collection&nbsp;<strong style='color:#60a5fa;'>{QDRANT_COLLECTION}</strong>
                &nbsp;·&nbsp;
                Top-k&nbsp;<strong style='color:#60a5fa;'>{MEMORY_SEARCH_LIMIT}</strong>
            </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Mermaid diagram ──────────────────────────────────────────────────────
    mermaid_code = f"""
flowchart TD
    User(["👤 User"])
    UI["🖥️ Streamlit UI<br/><small>app.py</small>"]
    Val{{"✅ Validate<br/>input"}}
    Err(["❌ Return error"])

    subgraph CHAIN["⛓️ LangChain Chain  —  memory_agent.py"]
        direction TB
        Prompt["📝 Build Prompt<br/><small>System + memories + question</small>"]
        LLM["🤖 ChatGoogleGenerativeAI<br/><small>{GEMINI_CHAT_MODEL}</small><br/><small>temp=0.3</small>"]
        Prompt --> LLM
    end

    subgraph MEM0["🧠 Mem0  —  Long-Term Memory Layer"]
        direction TB

        subgraph READ["READ  (every turn — before LLM)"]
            direction LR
            Search["memory.search()<br/><small>query = user message</small><br/><small>limit = {MEMORY_SEARCH_LIMIT}</small>"]
            EmbQ["Gemini Embedding<br/><small>{GEMINI_EMBEDDING_MODEL}</small><br/><small>embed query</small>"]
            QR[("🗄️ Qdrant<br/><small>cosine similarity</small>")]
            Search --> EmbQ --> QR
            QR -->|"top-{MEMORY_SEARCH_LIMIT} relevant<br/>memory snippets"| Search
        end

        subgraph WRITE["WRITE  (every turn — after LLM reply)"]
            direction LR
            Add["memory.add()<br/><small>user turn + assistant reply</small>"]
            Extract["Mem0 LLM<br/><small>{GEMINI_CHAT_MODEL}</small><br/><small>extract facts &amp; update graph</small>"]
            EmbF["Gemini Embedding<br/><small>embed new facts</small>"]
            QW[("🗄️ Qdrant<br/><small>upsert vectors</small><br/><small>./qdrant_data</small>")]
            Add --> Extract --> EmbF --> QW
        end
    end

    User -->|"types message"| UI
    UI -->|"chat(user_id, message)"| Val
    Val -->|"invalid"| Err
    Val -->|"valid"| Search
    Search -->|"formatted<br/>memory context"| Prompt
    LLM -->|"reply text"| UI
    UI -->|"display reply"| User
    LLM -->|"(user msg + reply)"| Add
    QW -.->|"persisted to disk<br/>survives restarts"| QR

    style MEM0  fill:#0d1e35,stroke:#2a4a6e,color:#7eb3d4
    style READ  fill:#0a1a2e,stroke:#1e3a5f,color:#7eb3d4
    style WRITE fill:#0a1a2e,stroke:#1e3a5f,color:#7eb3d4
    style CHAIN fill:#1a1d2e,stroke:#2a2d3e,color:#c9d1e0
    style User  fill:#1e3a5f,stroke:#3b82f6,color:#e8f4fd
    style UI    fill:#1a2535,stroke:#2a4a6e,color:#93c5fd
    style Val   fill:#1a2e1a,stroke:#166534,color:#4ade80
    style Err   fill:#2e1a1a,stroke:#991b1b,color:#f87171
    style QR    fill:#1a1535,stroke:#7c3aed,color:#c4b5fd
    style QW    fill:#1a1535,stroke:#7c3aed,color:#c4b5fd
"""

    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
            <style>
                body {{ margin:0; background:#0f1117; display:flex;
                        justify-content:center; padding:1rem; }}
                .mermaid {{ width:100%; max-width:960px; }}
                .mermaid svg {{ width:100% !important; height:auto !important; }}
            </style>
        </head>
        <body>
            <div class="mermaid">
{mermaid_code}
            </div>
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'dark',
                    themeVariables: {{
                        background:      '#0f1117',
                        primaryColor:    '#1e3a5f',
                        primaryBorderColor: '#3b82f6',
                        primaryTextColor:'#e8f4fd',
                        secondaryColor:  '#1a1d2e',
                        tertiaryColor:   '#13161f',
                        lineColor:       '#4b5563',
                        textColor:       '#c9d1e0',
                        fontSize:        '14px'
                    }},
                    flowchart: {{ curve: 'basis', padding: 20 }}
                }});
            </script>
        </body>
        </html>
        """,
        height=820,
        scrolling=True,
    )

    # ── Legend ──────────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """<div style='background:#0a1a2e;border:1px solid #1e3a5f;border-radius:12px;padding:1.2rem;'>
                <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:#3b82f6;margin-bottom:0.8rem;'>
                    🔵 Read path  (before LLM)
                </div>
                <div style='font-size:0.82rem;color:#7eb3d4;line-height:1.8;'>
                    1. User message is <b>embedded</b> by Gemini<br>
                    2. Qdrant runs <b>cosine similarity</b> search<br>
                    3. Top-{MEMORY_SEARCH_LIMIT} snippets injected into prompt<br>
                    4. LLM sees <b>personalised context</b>
                </div>
            </div>""".format(MEMORY_SEARCH_LIMIT=MEMORY_SEARCH_LIMIT),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""<div style='background:#0d1e0d;border:1px solid #166534;border-radius:12px;padding:1.2rem;'>
                <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:#4ade80;margin-bottom:0.8rem;'>
                    🟢 Write path  (after LLM)
                </div>
                <div style='font-size:0.82rem;color:#86efac;line-height:1.8;'>
                    1. Full turn passed to <b>Mem0</b><br>
                    2. Mem0 LLM <b>extracts facts</b> from conversation<br>
                    3. Facts are <b>embedded</b> and upserted into Qdrant<br>
                    4. Stored on disk — <b>survives restarts</b>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""<div style='background:#1a1535;border:1px solid #7c3aed;border-radius:12px;padding:1.2rem;'>
                <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:#a78bfa;margin-bottom:0.8rem;'>
                    🟣 Qdrant storage
                </div>
                <div style='font-size:0.82rem;color:#c4b5fd;line-height:1.8;'>
                    Collection&nbsp;<b>{QDRANT_COLLECTION}</b><br>
                    Dims&nbsp;<b>{GEMINI_EMBEDDING_MODEL.split("/")[-1]}&nbsp;768-d</b><br>
                    Path&nbsp;<b>./qdrant_data</b><br>
                    Shared by read <b>&amp;</b> write path
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
