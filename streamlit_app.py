"""Sprint Review Summarizer — Streamlit UI."""

import asyncio
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from app.agent import finalizer_agent, project_summarizer_agent
from app.tools import extract_project_chunks


# ---------------------------------------------------------------------------
# Environment & page config
# ---------------------------------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="Sprint Review Summarizer",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — premium dark theme
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
        color: #e2e8f0;
    }

    /* Hide default Streamlit header */
    #MainMenu, header, footer { visibility: hidden; }

    /* ---- Hero header ---- */
    .hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
    }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.4rem;
    }
    .hero p {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 300;
    }

    /* ---- Upload card ---- */
    .upload-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(167, 139, 250, 0.25);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(8px);
        transition: border-color 0.3s ease;
    }
    .upload-card:hover {
        border-color: rgba(167, 139, 250, 0.55);
    }

    /* ---- Section headers ---- */
    .section-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #a78bfa;
        margin-bottom: 0.6rem;
    }

    /* ---- Summary output card ---- */
    .summary-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(52, 211, 153, 0.25);
        border-radius: 16px;
        padding: 2rem 2.2rem;
        margin-top: 1.5rem;
        backdrop-filter: blur(8px);
        animation: fadeInUp 0.4s ease;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ---- Generate button ---- */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 2.2rem;
        font-size: 1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        transition: opacity 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35);
        width: 100%;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(124, 58, 237, 0.5);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ---- Dataframe ---- */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* ---- Spinner text ---- */
    .stSpinner > div {
        color: #a78bfa !important;
    }

    /* ---- Alert / error ---- */
    .stAlert {
        border-radius: 10px;
    }

    /* ---- Divider ---- */
    hr {
        border-color: rgba(255,255,255,0.08);
        margin: 1.5rem 0;
    }

    /* ---- Sidebar ---- */
    .css-1d391kg { background: rgba(255,255,255,0.03); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🏃 Sprint Review Summarizer</h1>
        <p>Upload your work-planning CSV and let the AI agent generate your weekly summary.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# API key check
# ---------------------------------------------------------------------------

api_key = os.getenv("GOOGLE_API_KEY", "")
if not api_key:
    st.warning(
        "⚠️  **GOOGLE_API_KEY not set.** Add it to a `.env` file in the project root and restart the app.",
        icon="🔑",
    )

# ---------------------------------------------------------------------------
# File uploader
# ---------------------------------------------------------------------------

st.markdown('<div class="upload-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">📂 Upload Work Planning CSV</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="Drop your CSV here",
    type=["csv"],
    label_visibility="collapsed",
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Preview + Generate
# ---------------------------------------------------------------------------

if uploaded_file is not None:
    csv_bytes = uploaded_file.read()
    csv_text = csv_bytes.decode("utf-8", errors="replace")

    # ── Data preview ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">👁️ Data Preview</div>', unsafe_allow_html=True)
    try:
        import io
        preview_df = pd.read_csv(io.StringIO(csv_text)).dropna(how="all")
        st.dataframe(preview_df, width="stretch", hide_index=True)
    except Exception as preview_err:
        st.error(f"Could not parse CSV for preview: {preview_err}")

    st.markdown("---")

    # ── Generate button ────────────────────────────────────────────────────
    col_btn, _ = st.columns([1, 2])
    with col_btn:
        generate = st.button("✨ Generate Summary", key="generate_btn", width="stretch")

    if generate:
        if not api_key:
            st.error("Cannot generate summary: GOOGLE_API_KEY is missing.")
        else:
            status_placeholder = st.empty()
            with status_placeholder.status("🤖 Running Sprint Review Pipeline...", expanded=True) as status_box:
                
                # ── Phase 1: Extract project chunks ──────────────────────────────
                status_box.write("📁 Slicing CSV data into project chunks (Skill 1)...")
                try:
                    chunks = extract_project_chunks(csv_text)
                    num_projects = len(chunks)
                    status_box.write(f"✓ Found {num_projects} active projects.")
                except Exception as chunk_err:
                    status_box.update(label="❌ Chunking Failed", state="error")
                    st.error(f"Failed to slice CSV: {chunk_err}")
                    st.stop()

                # ── Phase 2: Per-chunk summarization ─────────────────────────
                status_box.write(f"⚡ Summarizing {num_projects} projects (up to 5 concurrent calls)...")

                MAX_CONCURRENT = 1  # respect Gemini API rate limits

                async def summarize_one_chunk(
                    proj_name: str, chunk_md: str, semaphore: asyncio.Semaphore
                ) -> tuple[str, str]:
                    """Summarize a single project chunk in its own session."""
                    async with semaphore:
                        session_service = InMemorySessionService()
                        session = await session_service.create_session(
                            app_name="sprint_review",
                            user_id="streamlit_user",
                        )
                        runner = Runner(
                            agent=project_summarizer_agent,
                            app_name="sprint_review",
                            session_service=session_service,
                        )
                        user_message = genai_types.Content(
                            role="user",
                            parts=[
                                genai_types.Part(
                                    text=f"Summarize the following project chunk:\n\n{chunk_md}"
                                )
                            ],
                        )
                        result_parts: list[str] = []
                        print("Starting summarization for project:", proj_name)
                        async for event in runner.run_async(
                            user_id="streamlit_user",
                            session_id=session.id,
                            new_message=user_message,
                        ):
                            if event.content and event.content.parts:
                                for part in event.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        result_parts.append(part.text)
                        print("Finished summarization for project:", proj_name)
                        # Delay between calls to stay within free-tier rate limits
                        await asyncio.sleep(20)
                        return proj_name, "\n".join(result_parts).strip()

                async def run_all_summarizers(all_chunks: dict) -> str:
                    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
                    tasks = [
                        summarize_one_chunk(name, md, semaphore)
                        for name, md in all_chunks.items()
                    ]
                    results = await asyncio.gather(*tasks)
                    # Combine all summaries, separated by a divider
                    combined = []
                    for proj_name, summary in results:
                        combined.append(f"--- {proj_name} ---\n{summary}")
                    return "\n\n".join(combined)

                try:
                    all_summaries_text = asyncio.run(run_all_summarizers(chunks))
                    status_box.write(f"✓ Completed all {num_projects} project summaries.")
                except Exception as sum_err:
                    status_box.update(label="❌ Summarization Failed", state="error")
                    st.error(f"Failed to summarize projects: {sum_err}")
                    print(f"Failed to summarize projects: {sum_err}")
                    st.stop()

                # ── Phase 3: Finalize sprint review ──────────────────────────────
                status_box.write("✍ Compiling final 7-section weekly report (Skill 3)...")

                async def run_finalizer(summaries_text: str) -> str:
                    session_service = InMemorySessionService()
                    session = await session_service.create_session(
                        app_name="sprint_review",
                        user_id="streamlit_user",
                    )
                    runner = Runner(
                        agent=finalizer_agent,
                        app_name="sprint_review",
                        session_service=session_service,
                    )
                    user_message = genai_types.Content(
                        role="user",
                        parts=[
                            genai_types.Part(
                                text=(
                                    f"Please finalize the weekly sprint review from the following per-project summaries:\n\n"
                                    f"{summaries_text}"
                                )
                            )
                        ],
                    )
                    print("run_finalizer 1")
                    result_parts: list[str] = []
                    async for event in runner.run_async(
                        user_id="streamlit_user",
                        session_id=session.id,
                        new_message=user_message,
                    ):
                        print(event)
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    result_parts.append(part.text)
                    print("run_finalizer 3")
                    return "\n".join(result_parts).strip()

                try:
                    print("run_finalizer start")
                    summary_text = asyncio.run(run_finalizer(all_summaries_text))
                    print("run_finalizer end")
                    st.session_state["summary_result"] = summary_text
                    status_box.update(label="🎉 Pipeline Complete!", state="complete")
                except Exception as final_err:
                    status_box.update(label="❌ Finalization Failed", state="error")
                    st.error(f"Failed to finalize report: {final_err}")
                    print(f"Failed to finalize report: {final_err}")
                    st.stop()

    # ── Display results (persisted in session_state across reruns) ────────
    if "summary_result" in st.session_state and st.session_state["summary_result"]:
        summary_text = st.session_state["summary_result"]
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">📋 Sprint Summary</div>',
            unsafe_allow_html=True,
        )
        st.markdown(summary_text)
        st.markdown("</div>", unsafe_allow_html=True)

        # Download button
        st.download_button(
            label="⬇️ Download Summary as Markdown",
            data=summary_text,
            file_name="sprint_summary.md",
            mime="text/markdown",
        )


else:
    # ── Empty state illustration ───────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 3rem 1rem; color: #475569;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <p style="font-size: 1.1rem; font-weight: 500; color: #64748b;">
                Upload a CSV to get started
            </p>
            <p style="font-size: 0.9rem; color: #475569;">
                Expected format: <code>Assignee, Plan, Hours, Project 1, Project 2, ...</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
