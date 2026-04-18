import sys
sys.path.insert(1, r'D:\Notebooks\LLM\env')

import asyncio
import datetime
import streamlit as st
from mcp_playright import plan_urls, run_research

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- Global ---- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    min-height: 100vh;
}
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* ---- Hero banner ---- */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
    border-radius: 20px;
    padding: 40px 48px;
    margin-bottom: 32px;
    box-shadow: 0 20px 60px rgba(102,126,234,0.3);
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.hero h1 { color: #fff; font-size: 2.6rem; font-weight: 800; margin: 0 0 8px 0; }
.hero p  { color: rgba(255,255,255,0.82); font-size: 1.05rem; margin: 0; }

/* ---- Search card ---- */
.search-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 28px 32px;
    backdrop-filter: blur(12px);
    margin-bottom: 28px;
}

/* ---- Source pills ---- */
.pill-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0; }
.pill {
    background: rgba(102,126,234,0.18);
    border: 1px solid rgba(102,126,234,0.40);
    color: #a5b4fc;
    border-radius: 100px;
    padding: 6px 14px;
    font-size: 0.78rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 320px;
    display: inline-block;
}
.pill a { color: #a5b4fc; text-decoration: none; }
.pill a:hover { color: #fff; }

/* ---- Step tracker ---- */
.step-bar {
    display: flex; gap: 0; margin: 24px 0;
    border-radius: 12px; overflow: hidden;
}
.step {
    flex: 1; text-align: center;
    padding: 10px 8px; font-size: 0.80rem; font-weight: 600;
    border-right: 1px solid rgba(0,0,0,0.2);
    transition: all 0.3s;
}
.step:last-child { border-right: none; }
.step-done  { background: #22c55e; color: #fff; }
.step-active{ background: #667eea; color: #fff; animation: pulse 1.5s infinite; }
.step-wait  { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.35); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }

/* ---- Result card ---- */
.result-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 28px 32px;
    margin-top: 24px;
    line-height: 1.8;
}
.result-header {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.result-header h3 { color: #fff; margin: 0; font-size: 1.2rem; }
.badge {
    background: linear-gradient(90deg,#667eea,#764ba2);
    color: #fff; border-radius: 8px; padding: 4px 12px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;
}

/* ---- Sidebar history card ---- */
.hist-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: border-color 0.2s;
}
.hist-card:hover { border-color: rgba(102,126,234,0.50); }
.hist-time { color: rgba(255,255,255,0.35); font-size: 0.72rem; }
.hist-task { color: rgba(255,255,255,0.80); font-size: 0.88rem; font-weight: 500; }

/* ---- Stat tiles ---- */
.stat-row { display: flex; gap: 12px; margin: 12px 0 20px; }
.stat-tile {
    flex: 1; background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 14px 10px; text-align: center;
}
.stat-tile .val { color: #a5b4fc; font-size: 1.6rem; font-weight: 800; }
.stat-tile .lbl { color: rgba(255,255,255,0.40); font-size: 0.72rem; margin-top: 2px; }

/* ---- Log entry ---- */
.log-line {
    font-family: monospace; font-size: 0.80rem;
    color: rgba(255,255,255,0.50);
    padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.log-line span { color: #4ade80; margin-right: 8px; }

/* ---- Override Streamlit defaults ---- */
h1,h2,h3,h4,p,label,li,td,th,span,div { color: #e2e8f0 !important; }

/* Textarea — dark transparent with readable light text */
textarea,
.stTextArea textarea,
[data-testid="stTextArea"] textarea,
[data-baseweb="textarea"] textarea,
div[data-testid="stTextArea"] > div > textarea,
section[data-testid="stMain"] textarea {
    background-color: rgba(20, 20, 40, 0.75) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(102,126,234,0.35) !important;
    border-radius: 12px !important;
    font-size: 0.96rem !important;
    line-height: 1.7 !important;
    caret-color: #a5b4fc !important;
}
textarea::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: rgba(180,190,220,0.45) !important;
}
textarea:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.22) !important;
    outline: none !important;
    background-color: rgba(20, 20, 45, 0.88) !important;
}

/* Selectbox (example picker) */
[data-baseweb="select"] > div,
[data-testid="stSelectbox"] > div > div {
    background-color: rgba(20, 20, 40, 0.75) !important;
    border: 1px solid rgba(102,126,234,0.35) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* Result markdown — ensure all text is light and readable */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stMarkdownContainer"] td,
[data-testid="stMarkdownContainer"] th {
    color: #dde3f0 !important;
}
[data-testid="stMarkdownContainer"] a {
    color: #a5b4fc !important;
}
[data-testid="stMarkdownContainer"] code {
    background: rgba(102,126,234,0.15) !important;
    color: #c4b5fd !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
}
[data-testid="stMarkdownContainer"] blockquote {
    border-left: 3px solid #667eea !important;
    background: rgba(102,126,234,0.08) !important;
    padding: 10px 16px !important;
    border-radius: 0 8px 8px 0 !important;
    color: #c4cde0 !important;
}
[data-testid="stMarkdownContainer"] table {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stMarkdownContainer"] th {
    background: rgba(102,126,234,0.20) !important;
}
[data-testid="stMarkdownContainer"] tr:nth-child(even) td {
    background: rgba(255,255,255,0.03) !important;
}

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #c8cfe0 !important; }

/* Primary button */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border: none !important; border-radius: 12px !important;
    font-weight: 700 !important; font-size: 0.95rem !important;
    padding: 12px 24px !important; color: #fff !important;
    box-shadow: 0 4px 20px rgba(102,126,234,0.40) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(102,126,234,0.55) !important;
}
.stAlert { border-radius: 12px !important; }
[data-testid="stExpander"] { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "running" not in st.session_state:
    st.session_state.running = False

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 AI Research Agent")
    st.caption("Playwright MCP · GPT-4o")
    st.divider()

    total = len(st.session_state.history)
    sources_browsed = sum(len(h.get("urls", [])) for h in st.session_state.history)

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-tile"><div class="val">{total}</div><div class="lbl">Searches</div></div>
        <div class="stat-tile"><div class="val">{sources_browsed}</div><div class="lbl">Pages browsed</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🕑 Recent Searches")

    if not st.session_state.history:
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.85rem;">No searches yet. Ask anything above!</p>', unsafe_allow_html=True)
    else:
        if st.button("🗑 Clear all history", use_container_width=True):
            st.session_state.history = []
            st.rerun()

        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"🔎 {item['task'][:45]}{'…' if len(item['task']) > 45 else ''}", expanded=False):
                st.caption(f"🕐 {item['timestamp']}  ·  {len(item.get('urls', []))} sources")
                st.markdown(item["result"])
                st.download_button(
                    label="⬇ Download",
                    data=item["result"],
                    file_name=f"research_{i+1}.txt",
                    mime="text/plain",
                    key=f"dl_hist_{i}",
                    use_container_width=True,
                )

    st.divider()
    st.markdown('<p style="color:rgba(255,255,255,0.2);font-size:0.72rem;text-align:center;">Built with LangChain · LangGraph · Playwright MCP</p>', unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🔍 AI Web Research Agent</h1>
    <p>Ask anything — flights, prices, news, comparisons. The agent browses the web in real time and delivers a structured answer.</p>
</div>
""", unsafe_allow_html=True)

# ── Input card ─────────────────────────────────────────────────────────────────
st.markdown('<div class="search-card">', unsafe_allow_html=True)

example_tasks = [
    "💼 Select a task to try →",
    "✈ Flights from Delhi to Dubai next month",
    "📱 Compare iPhone 16 Pro prices in India",
    "🏨 Budget hotels in Bali near the beach",
    "📚 Best Python AI courses online under $50",
    "🏎 Tesla Model 3 vs Model Y — price & range",
]
selected_example = st.selectbox("Quick examples", example_tasks, label_visibility="collapsed")

prefill = "" if selected_example.startswith("💼") else selected_example[2:].strip()

user_task = st.text_area(
    label="Your research task",
    value=prefill,
    placeholder=(
        "e.g. Find me the cheapest return flights from Singapore to Tokyo in July\n"
        "e.g. What is the current price of gold per gram in India?\n"
        "e.g. Compare MacBook Pro M4 vs Dell XPS 15 specs and price"
    ),
    height=110,
    disabled=st.session_state.running,
    label_visibility="collapsed",
)

col_hint, col_btn = st.columns([4, 1], vertical_alignment="bottom")
with col_hint:
    st.caption("💡 The agent will plan search URLs, browse live pages, and synthesise a structured answer.")
with col_btn:
    submit = st.button(
        "🚀  Research Now",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running or not user_task.strip(),
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Research flow ──────────────────────────────────────────────────────────────
if submit and user_task.strip():
    st.session_state.running = True
    task = user_task.strip()

    # ── Step 1: plan URLs ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="step-bar">
        <div class="step step-active">① Planning</div>
        <div class="step step-wait">② Browsing</div>
        <div class="step step-wait">③ Synthesising</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Analysing your task and planning search strategy..."):
        try:
            urls, synthesis_instruction = plan_urls(task)
        except Exception as e:
            st.error(f"**Planning failed.** {e}")
            st.session_state.running = False
            st.stop()

    # Show sources as pills
    pills_html = "".join(
        f'<span class="pill"><a href="{u}" target="_blank">🌐 {u[:55]}{"…" if len(u)>55 else ""}</a></span>'
        for u in urls
    )
    st.markdown(f"""
    <div style="margin:4px 0 8px;">
        <span style="color:rgba(255,255,255,0.45);font-size:0.80rem;">
            ✅ Strategy ready — will browse <b style="color:#a5b4fc">{len(urls)}</b> source(s):
        </span>
    </div>
    <div class="pill-row">{pills_html}</div>
    """, unsafe_allow_html=True)

    # ── Step 2: browse ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="step-bar">
        <div class="step step-done">✓ Planning</div>
        <div class="step step-active">② Browsing</div>
        <div class="step step-wait">③ Synthesising</div>
    </div>
    """, unsafe_allow_html=True)

    logs: list[str] = []
    result_text = ""
    error_text = ""

    def on_status(msg: str):
        logs.append(msg)

    with st.spinner("Launching browser and collecting data...  *(~30–60 s)*"):
        try:
            result_text = asyncio.run(
                run_research(task, urls, synthesis_instruction, on_status=on_status)
            )
        except Exception as e:
            error_text = str(e) 

    # ── Step 3: display ────────────────────────────────────────────────────────
    if error_text:
        st.markdown("""
        <div class="step-bar">
            <div class="step step-done">✓ Planning</div>
            <div class="step step-done">✓ Browsing</div>
            <div class="step" style="background:#ef4444;color:#fff;">✗ Error</div>
        </div>
        """, unsafe_allow_html=True)
        st.error(f"**Research failed:** {error_text}")

    else:
        st.markdown("""
        <div class="step-bar">
            <div class="step step-done">✓ Planning</div>
            <div class="step step-done">✓ Browsing</div>
            <div class="step step-done">✓ Synthesised</div>
        </div>
        """, unsafe_allow_html=True)

        # Browse log (collapsed by default)
        if logs:
            with st.expander("📡 Browse activity log", expanded=False):
                log_html = "".join(
                    f'<div class="log-line"><span>▶</span>{l}</div>'
                    for l in logs
                )
                st.markdown(log_html, unsafe_allow_html=True)

        # Result card
        now = datetime.datetime.now().strftime("%d %b %Y · %H:%M")
        st.markdown(f"""
        <div class="result-card">
            <div class="result-header">
                <span style="font-size:1.5rem">📋</span>
                <h3>Research Result</h3>
                <span class="badge">GPT-4o</span>
                <span style="color:rgba(255,255,255,0.30);font-size:0.78rem;margin-left:auto">{now}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(result_text)

        col_dl, col_spacer = st.columns([1, 3])
        with col_dl:
            st.download_button(
                label="⬇ Download result",
                data=result_text,
                file_name=f"research_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # Save to session history
        st.session_state.history.append({
            "task": task,
            "urls": urls,
            "result": result_text,
            "timestamp": now,
        })

    st.session_state.running = False
