"""Generate architecture.png  —  simple flow diagram focused on Mem0."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT = Path(__file__).parent / "architecture.png"

# ── colours ──────────────────────────────────────────────────────────────────
BG      = "#0f1117"
BLUE_D  = "#1e3a5f"
BLUE_L  = "#3b82f6"
BLUE_T  = "#60a5fa"
GREEN_D = "#14532d"
GREEN_L = "#4ade80"
GREEN_T = "#86efac"
PURP_D  = "#3b0764"
PURP_L  = "#a78bfa"
TEAL    = "#22d3ee"
ORANGE  = "#fb923c"
GREY_D  = "#1a1d2e"
GREY_B  = "#2a2d3e"
WHITE   = "#e8f4fd"
DIM     = "#6b7280"
SUBT    = "#7eb3d4"

fig, ax = plt.subplots(figsize=(13, 20))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 13)
ax.set_ylim(0, 20)
ax.axis("off")

# ── helpers ───────────────────────────────────────────────────────────────────

def rbox(x, y, w, h, fc, ec, lw=1.8, r=0.3, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))

def t(x, y, s, sz=9, c=WHITE, ha="center", va="center", bold=False, z=5):
    ax.text(x, y, s, fontsize=sz, color=c, ha=ha, va=va, zorder=z,
            fontweight="bold" if bold else "normal")

def arr(x1, y1, x2, y2, c=DIM, lw=1.8, rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=4,
                arrowprops=dict(arrowstyle="-|>", color=c, lw=lw,
                                mutation_scale=14,
                                connectionstyle=f"arc3,rad={rad}"))

# ─────────────────────────────────────────────────────────────────────────────
#  TITLE
# ─────────────────────────────────────────────────────────────────────────────
rbox(0.3, 19.1, 12.4, 0.75, BLUE_D, BLUE_L, lw=2, r=0.35)
t(6.5, 19.54, "AI Interview Prep Coach — Memory Flow", sz=13, bold=True)
t(6.5, 19.18, "Mem0  ·  Qdrant  ·  Gemini  ·  LangChain", sz=8.5, c=SUBT)

# ─────────────────────────────────────────────────────────────────────────────
#  1. USER
# ─────────────────────────────────────────────────────────────────────────────
rbox(4.25, 17.5, 4.5, 0.95, BLUE_D, BLUE_L, lw=2.2, r=0.4, z=3)
t(6.5, 18.05, "👤  User", sz=11, bold=True)
t(6.5, 17.72, "sends a message", sz=8, c=SUBT)

arr(6.5, 17.5, 6.5, 16.75, c=BLUE_L, lw=2)
t(7.4, 17.12, "user message", sz=8, c=BLUE_T)

# ─────────────────────────────────────────────────────────────────────────────
#  2. STREAMLIT UI
# ─────────────────────────────────────────────────────────────────────────────
rbox(3.0, 15.6, 7.0, 1.05, GREY_D, GREY_B, lw=1.8, r=0.35, z=3)
t(6.5, 16.19, "🖥️  Streamlit UI  —  app.py", sz=10, c=BLUE_T, bold=True)
t(6.5, 15.82, "calls  chat(user_id, message)", sz=8, c=SUBT)

arr(6.5, 15.6, 6.5, 14.85, c=BLUE_L, lw=2)
t(7.6, 15.22, "chat( )", sz=8, c=BLUE_T)

# ─────────────────────────────────────────────────────────────────────────────
#  MEM0 BIG CONTAINER
# ─────────────────────────────────────────────────────────────────────────────
rbox(0.3, 2.5, 12.4, 12.15, "#0d1e35", BLUE_L, lw=2.5, r=0.55, z=2)
t(0.9, 14.36, "🧠  Mem0  —  Long-Term Memory Layer", sz=11,
  c=BLUE_T, ha="left", bold=True)
t(0.9, 13.98, "persists facts across sessions  ·  semantic retrieval via embeddings",
  sz=7.5, c=DIM, ha="left")

# ── READ box ──────────────────────────────────────────────────────────────────
rbox(0.65, 11.4, 11.7, 2.4, "#091525", BLUE_L, lw=1.8, r=0.4, z=3)
t(1.2, 13.5, "READ  —  before LLM call", sz=9, c=BLUE_T, ha="left", bold=True)

#   memory.search()
rbox(0.85, 11.65, 3.0, 1.6, "#0f2035", BLUE_L, lw=1.5, r=0.28, z=4)
t(2.35, 12.85, "memory.search()", sz=8.5, c=BLUE_T, bold=True)
t(2.35, 12.55, "query = user message", sz=7.5, c=SUBT)
t(2.35, 12.25, "limit = 5", sz=7.5, c=SUBT)
t(2.35, 11.95, "returns relevant facts", sz=7, c=DIM)

#   Gemini Embed (read)
rbox(4.65, 11.65, 3.3, 1.6, "#0a1c28", TEAL, lw=1.5, r=0.28, z=4)
t(6.3, 12.85, "Gemini Embedding", sz=8.5, c=TEAL, bold=True)
t(6.3, 12.55, "gemini-embedding-001", sz=7.5, c=SUBT)
t(6.3, 12.25, "768-dim vectors", sz=7.5, c=SUBT)
t(6.3, 11.95, "embeds the query", sz=7, c=DIM)

#   Qdrant
rbox(8.7, 11.45, 3.3, 2.1, "#130f2e", PURP_L, lw=2, r=0.32, z=4)
t(10.35, 13.1, "🗄️  Qdrant", sz=9.5, c=PURP_L, bold=True)
t(10.35, 12.75, "Vector Store", sz=8, c=SUBT)
t(10.35, 12.45, "cosine similarity", sz=7.5, c="#c4b5fd")
t(10.35, 12.15, "./qdrant_data", sz=7.5, c=PURP_L)
t(10.35, 11.82, "💾 on disk", sz=7.5, c=GREEN_L)

# arrows inside READ
arr(3.85, 12.45, 4.65, 12.45, c=BLUE_L, lw=1.6)
t(4.25, 12.65, "embed", sz=7, c=DIM)
arr(7.95, 12.45, 8.7, 12.45, c=TEAL, lw=1.6)
t(8.32, 12.65, "vector", sz=7, c=DIM)
# return arrow (Qdrant → search, below)
arr(8.7, 11.75, 3.85, 11.75, c=PURP_L, lw=1.6, rad=0.0)
t(6.25, 11.55, "top-5 relevant memory snippets", sz=7.5, c="#c4b5fd")

arr(6.5, 11.4, 6.5, 10.65, c=BLUE_T, lw=2)
t(7.7, 11.02, "memory context", sz=8, c=BLUE_T)

# ── LANGCHAIN CHAIN box ───────────────────────────────────────────────────────
rbox(0.65, 8.1, 11.7, 2.3, "#131620", GREY_B, lw=1.8, r=0.4, z=3)
t(1.2, 10.12, "⛓️  LangChain Chain", sz=9, c=WHITE, ha="left", bold=True)

#   Prompt template
rbox(0.85, 8.35, 4.7, 1.6, "#10131e", GREY_B, lw=1.4, r=0.28, z=4)
t(3.2, 9.55, "📝 Prompt Template", sz=8.5, c=WHITE, bold=True)
t(3.2, 9.25, "System instructions", sz=7.5, c=SUBT)
t(3.2, 8.97, "{memories}  ← 5 snippets", sz=7.5, c=BLUE_T)
t(3.2, 8.68, "{question}  ← user msg", sz=7.5, c=SUBT)

#   Gemini LLM
rbox(6.7, 8.35, 5.3, 1.6, "#101525", BLUE_L, lw=1.8, r=0.28, z=4)
t(9.35, 9.55, "🤖 ChatGoogleGenerativeAI", sz=8.5, c=BLUE_T, bold=True)
t(9.35, 9.25, "gemini-2.5-flash-lite", sz=8, c=WHITE)
t(9.35, 8.97, "temperature = 0.3", sz=7.5, c=SUBT)
t(9.35, 8.68, "generates reply", sz=7.5, c=SUBT)

arr(5.55, 9.15, 6.7, 9.15, c=BLUE_L, lw=1.8)
t(6.12, 9.38, "invoke", sz=7.5, c=BLUE_T)

arr(6.5, 8.1, 6.5, 7.35, c=GREEN_L, lw=2)
t(7.65, 7.72, "reply text", sz=8, c=GREEN_L)

# Reply back to UI (right side curved arrow up)
arr(11.7, 9.15, 9.6, 15.6, c=ORANGE, lw=2, rad=-0.28)
t(12.55, 12.5, "reply\nto UI", sz=8.5, c=ORANGE)

# ── WRITE box ─────────────────────────────────────────────────────────────────
rbox(0.65, 2.75, 11.7, 4.4, "#091a0d", GREEN_D, lw=1.8, r=0.4, z=3)
t(1.2, 6.88, "WRITE  —  after every LLM reply", sz=9, c=GREEN_L, ha="left", bold=True)
t(1.2, 6.55, "Mem0 extracts facts from the conversation — not raw text",
  sz=7.5, c=DIM, ha="left")

#   memory.add()
rbox(0.85, 2.95, 2.8, 3.2, "#0a200a", GREEN_D, lw=1.5, r=0.28, z=4)
t(2.25, 5.75, "memory.add()", sz=8.5, c=GREEN_L, bold=True)
t(2.25, 5.42, "receives:", sz=7.5, c=GREEN_T)
t(2.25, 5.12, "user message", sz=7.5, c=GREEN_T)
t(2.25, 4.82, "+ assistant reply", sz=7.5, c=GREEN_T)
t(2.25, 4.5,  "full turn context", sz=7.5, c=GREEN_T)
t(2.25, 4.18, "passed to Mem0", sz=7, c=DIM)
t(2.25, 3.88, "for processing", sz=7, c=DIM)
t(2.25, 3.2,  "→ entry point", sz=7.5, c=GREEN_L, bold=True)

#   LLM fact extraction
rbox(4.4, 2.95, 3.2, 3.2, "#0f1f0f", "#15803d", lw=1.5, r=0.28, z=4)
t(6.0, 5.75, "🤖 Fact Extraction", sz=8.5, c=GREEN_L, bold=True)
t(6.0, 5.42, "gemini-2.5-flash-lite", sz=7.5, c=GREEN_T)
t(6.0, 5.1,  "reads exchange &", sz=7.5, c=GREEN_T)
t(6.0, 4.8,  "extracts discrete", sz=7.5, c=GREEN_T)
t(6.0, 4.5,  "facts / entities", sz=7.5, c=GREEN_T)
t(6.0, 4.18, "e.g. 'targets SWE'", sz=7, c=DIM, bold=False)
t(6.0, 3.88, "'weak: system design'", sz=7, c=DIM)
t(6.0, 3.55, "'studied: Python OOP'", sz=7, c=DIM)

#   Gemini Embed (write)
rbox(8.3, 2.95, 3.1, 3.2, "#0a1c20", TEAL, lw=1.5, r=0.28, z=4)
t(9.85, 5.75, "Gemini Embedding", sz=8.5, c=TEAL, bold=True)
t(9.85, 5.42, "gemini-embedding-001", sz=7.5, c=SUBT)
t(9.85, 5.1,  "embeds each", sz=7.5, c=SUBT)
t(9.85, 4.8,  "extracted fact", sz=7.5, c=SUBT)
t(9.85, 4.5,  "768-dim vector", sz=7.5, c=SUBT)
t(9.85, 4.18, "for semantic", sz=7, c=DIM)
t(9.85, 3.88, "similarity later", sz=7, c=DIM)

# Qdrant write (reuses same store — dotted line up to READ Qdrant)
ax.plot([10.35, 10.35], [6.2, 11.45], color=PURP_L,
        lw=1.8, linestyle=(0, (5, 4)), alpha=0.55, zorder=2)
t(11.4, 8.85, "same\nstore", sz=7.5, c="#c4b5fd", ha="center")

# arrows inside WRITE
arr(3.65, 4.55, 4.4, 4.55, c=GREEN_L, lw=1.6)
t(4.02, 4.78, "turn", sz=7, c=DIM)
arr(7.6, 4.55, 8.3, 4.55, c=GREEN_L, lw=1.6)
t(7.95, 4.78, "facts", sz=7, c=DIM)
arr(11.4, 4.55, 10.35, 7.15, c=TEAL, lw=1.6, rad=0.1)
t(11.7, 5.9, "upsert\nvectors", sz=7.5, c=TEAL)

# ─────────────────────────────────────────────────────────────────────────────
#  Reply:  UI → User
# ─────────────────────────────────────────────────────────────────────────────
arr(6.5, 16.65, 6.5, 17.5, c=ORANGE, lw=2)
t(5.5, 17.08, "reply", sz=8, c=ORANGE)

# ─────────────────────────────────────────────────────────────────────────────
#  LEGEND
# ─────────────────────────────────────────────────────────────────────────────
rbox(0.3, 0.18, 12.4, 2.15, "#0d1117", GREY_B, r=0.35, lw=1.4)
t(0.8, 2.08, "Legend", sz=8, c=DIM, ha="left", bold=True)

items = [
    (BLUE_L,  "User / UI flow"),
    (BLUE_T,  "READ — memory retrieval (before LLM)"),
    (GREEN_L, "WRITE — fact storage (after LLM)"),
    (PURP_L,  "Qdrant — shared disk-persisted vector store"),
    (TEAL,    "Gemini embedding model"),
    (ORANGE,  "Reply path back to user"),
]
for i, (color, label) in enumerate(items):
    col, row = i % 3, i // 3
    lx = 0.9 + col * 4.2
    ly = 1.68 - row * 0.55
    ax.plot(lx, ly, "o", color=color, markersize=9, zorder=6)
    t(lx + 0.25, ly, label, sz=8, c=SUBT, ha="left")

# ─────────────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0)
plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
plt.close(fig)
print(f"Saved → {OUT}")
