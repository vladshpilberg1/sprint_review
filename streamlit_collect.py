"""Sprint Data Collection — Streamlit UI.

A separate Streamlit page that collects weekly sprint data from individual
team members through an AI-guided interview, stores responses in session
state, and compiles them into a CSV matching the existing work-planning
template format.

Run with:  streamlit run streamlit_collect.py
"""

import asyncio
import json
import os
import re
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from app.csv_compiler import compile_week_csv
from app.data_collection_agent import data_collection_agent
from app.security import sanitize

# ---------------------------------------------------------------------------
# Environment & page config
# ---------------------------------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="Sprint Data Collection",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — premium dark theme (consistent with the review app)
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
        background: linear-gradient(90deg, #f59e0b, #f97316, #ef4444);
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

    /* ---- Cards ---- */
    .form-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(245, 158, 11, 0.25);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(8px);
        transition: border-color 0.3s ease;
    }
    .form-card:hover {
        border-color: rgba(245, 158, 11, 0.55);
    }

    .compile-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(52, 211, 153, 0.25);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(8px);
        transition: border-color 0.3s ease;
    }
    .compile-card:hover {
        border-color: rgba(52, 211, 153, 0.55);
    }

    .status-card {
        background: rgba(52, 211, 153, 0.08);
        border: 1px solid rgba(52, 211, 153, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
    }

    /* ---- Section headers ---- */
    .section-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #f59e0b;
        margin-bottom: 0.6rem;
    }
    .section-label-green {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #34d399;
        margin-bottom: 0.6rem;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b, #ef4444);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 2.2rem;
        font-size: 1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        transition: opacity 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.35);
        width: 100%;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(245, 158, 11, 0.5);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ---- Download button ---- */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669, #10b981) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.65rem 2.2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.35) !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        opacity: 0.9 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.5) !important;
    }

    /* ---- Chat styling ---- */
    .stChatMessage {
        border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stChatMessage p,
    .stChatMessage li,
    .stChatMessage span,
    .stChatMessage div,
    .stChatMessage strong,
    .stChatMessage em,
    .stChatMessage code {
        color: #f1f5f9 !important;
    }
    .stChatMessage strong {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] + div p,
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] + div li {
        color: #e2e8f0 !important;
    }

    /* ---- Spinner text ---- */
    .stSpinner > div {
        color: #f59e0b !important;
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

    /* ---- Selectbox / multiselect tweaks ---- */
    .stSelectbox label, .stMultiSelect label, .stDateInput label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USERS = ["Alex", "Bob", "Elvin", "Dan"]

# Project name → type mapping
PROJECTS = {
    "Feature A for Company Initech": "Delivery",
    "Model Migration for company Dunder Mifflin": "Delivery",
    "Enhance routing capabilities": "Refinement",
    "Improve code coverage to > 90%": "Operations",
    "Create automated test suite": "Operations",
}

PROJECT_NAMES = list(PROJECTS.keys())

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_fridays(num_past: int = 8, num_future: int = 4) -> tuple[list[date], int]:
    """Return a list of Fridays and the index of the current-week Friday."""
    today = date.today()
    weekday = today.weekday()  # 0=Mon … 4=Fri … 6=Sun
    if weekday <= 4:
        current_friday = today + timedelta(days=4 - weekday)
    else:
        current_friday = today - timedelta(days=weekday - 4)

    fridays = [current_friday + timedelta(weeks=i) for i in range(-num_past, num_future + 1)]
    default_idx = fridays.index(current_friday)
    return fridays, default_idx


def extract_json_from_response(response: str) -> dict | None:
    """Extract the first ```json … ``` block from an agent response."""
    match = re.search(r"```json\s*\n(.*?)\n\s*```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


# ── ADK helpers ──────────────────────────────────────────────────────────

async def _create_session() -> tuple:
    """Create a fresh InMemorySessionService + session."""
    service = InMemorySessionService()
    session = await service.create_session(
        app_name="sprint_data_collection",
        user_id="collector",
    )
    return service, session.id


async def _send_message(service, session_id: str, text: str) -> str:
    """Send a user message to the data-collection agent and return its reply."""
    # ── Security checkpoint ──────────────────────────────────────────────
    text, sec_report = sanitize(text)
    if sec_report["pii_categories_redacted"]:
        print(f"[SECURITY] PII scrubbed: {sec_report['pii_categories_redacted']}")
    if sec_report["prompt_injection_detected"]:
        print("[SECURITY] Prompt injection attempt blocked")

    runner = Runner(
        agent=data_collection_agent,
        app_name="sprint_data_collection",
        session_service=service,
    )
    msg = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=text)],
    )
    parts: list[str] = []
    async for event in runner.run_async(
        user_id="collector",
        session_id=session_id,
        new_message=msg,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    parts.append(part.text)
    return "\n".join(parts).strip()


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "submissions": {},          # (user, friday_date) → parsed JSON
    "chat_messages": [],        # [{"role": …, "content": …}, …]
    "chat_active": False,
    "interview_complete": False,
    "adk_session_service": None,
    "adk_session_id": None,
    "current_user": None,
    "current_week": None,
    "current_projects": [],
    "compiled_csv": None,
    "compiled_filename": None,
    "input_key_counter": 0,     # bump to clear the text_area after send
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>📝 Sprint Data Collection</h1>
        <p>Report your weekly progress through an AI-guided interview and compile the team CSV.</p>
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
        "⚠️  **GOOGLE_API_KEY not set.** Add it to a `.env` file in the project root and restart.",
        icon="🔑",
    )

# ---------------------------------------------------------------------------
# Form controls
# ---------------------------------------------------------------------------

st.markdown('<div class="form-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">🎯 Sprint Details</div>', unsafe_allow_html=True)

fridays, default_friday_idx = get_fridays()
is_locked = st.session_state.chat_active  # lock controls during interview

col1, col2 = st.columns(2)

with col1:
    selected_user = st.selectbox(
        "👤 Your name",
        options=USERS,
        index=None,
        placeholder="Select your name…",
        disabled=is_locked,
    )

with col2:
    selected_friday = st.selectbox(
        "📅 Reporting week (Friday)",
        options=fridays,
        index=default_friday_idx,
        format_func=lambda d: d.strftime("%b %d, %Y"),
        disabled=is_locked,
    )

selected_projects = st.multiselect(
    "📋 Projects you worked on / plan to work on",
    options=PROJECT_NAMES,
    disabled=is_locked,
)

# Submit button
can_submit = (
    selected_user is not None
    and len(selected_projects) > 0
    and not is_locked
    and api_key
)

if st.button("🚀 Start Interview", disabled=not can_submit, key="start_btn"):
    # Create a fresh ADK session
    service, session_id = asyncio.run(_create_session())
    st.session_state.adk_session_service = service
    st.session_state.adk_session_id = session_id
    st.session_state.chat_active = True
    st.session_state.interview_complete = False
    st.session_state.chat_messages = []
    st.session_state.current_user = selected_user
    st.session_state.current_week = selected_friday
    st.session_state.current_projects = selected_projects

    # Initial context message to the agent
    project_list = "\n".join(
        f"- {p} (Type: {PROJECTS[p]})" for p in selected_projects
    )
    context_msg = (
        f"You are interviewing **{selected_user}** about their sprint progress "
        f"for the week ending **{selected_friday.strftime('%B %d, %Y')}**.\n\n"
        f"They are working on the following projects:\n{project_list}\n\n"
        f"Please start the interview by asking about the first project. "
        f"Remember to gather: (1) what was planned & hours, (2) what was achieved & hours, "
        f"(3) dependencies & risks, (4) next week plan & hours."
    )

    with st.spinner("Starting interview…"):
        response = asyncio.run(_send_message(service, session_id, context_msg))
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat section (visible when interview is active or just completed)
# ---------------------------------------------------------------------------

if st.session_state.chat_active or st.session_state.interview_complete:
    st.markdown("---")
    st.markdown(
        '<div class="section-label">💬 Sprint Interview</div>',
        unsafe_allow_html=True,
    )

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Inline input area (between messages and Finish button) ────────────
    if st.session_state.chat_active and not st.session_state.interview_complete:
        input_key = f"user_input_{st.session_state.input_key_counter}"
        user_input = st.text_area(
            "Your response",
            key=input_key,
            placeholder="Type your response here…",
            height=100,
            label_visibility="collapsed",
        )

        send_col, finish_col, _ = st.columns([1, 1, 2])

        with send_col:
            send_clicked = st.button("➤ Send", key="send_btn", use_container_width=True)

        with finish_col:
            finish_clicked = st.button(
                "📋 Finish & Compile Now",
                key="finish_btn",
                help="Ask the agent to compile all information gathered so far into the final JSON.",
                use_container_width=True,
            )

        # ── Handle send ──────────────────────────────────────────────────
        if send_clicked and user_input and user_input.strip():
            prompt = user_input.strip()
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            with st.spinner("Agent is thinking…"):
                response = asyncio.run(
                    _send_message(
                        st.session_state.adk_session_service,
                        st.session_state.adk_session_id,
                        prompt,
                    )
                )
            st.session_state.chat_messages.append({"role": "assistant", "content": response})

            # Check for JSON completion
            parsed = extract_json_from_response(response)
            if parsed:
                key = (st.session_state.current_user, st.session_state.current_week)
                st.session_state.submissions[key] = parsed
                st.session_state.interview_complete = True
                st.session_state.chat_active = False

            # Bump key counter to clear the text area on rerun
            st.session_state.input_key_counter += 1
            st.rerun()

        # ── Handle finish early ──────────────────────────────────────────
        if finish_clicked:
            finish_msg = (
                "Please compile all the information we have discussed so far and "
                "output the final JSON summary now, even if some projects are incomplete."
            )
            st.session_state.chat_messages.append({"role": "user", "content": finish_msg})
            with st.spinner("Compiling…"):
                response = asyncio.run(
                    _send_message(
                        st.session_state.adk_session_service,
                        st.session_state.adk_session_id,
                        finish_msg,
                    )
                )
            st.session_state.chat_messages.append({"role": "assistant", "content": response})

            parsed = extract_json_from_response(response)
            if parsed:
                key = (st.session_state.current_user, st.session_state.current_week)
                st.session_state.submissions[key] = parsed
                st.session_state.interview_complete = True
                st.session_state.chat_active = False

            st.session_state.input_key_counter += 1
            st.rerun()

    # Completion notice
    if st.session_state.interview_complete:
        st.markdown(
            '<div class="status-card">'
            "✅ <strong>Interview complete!</strong> Your responses have been recorded."
            "</div>",
            unsafe_allow_html=True,
        )

        if st.button("🔄 Start New Interview", key="new_interview_btn"):
            st.session_state.chat_active = False
            st.session_state.interview_complete = False
            st.session_state.chat_messages = []
            st.session_state.adk_session_service = None
            st.session_state.adk_session_id = None
            st.session_state.input_key_counter = 0
            st.rerun()

# ---------------------------------------------------------------------------
# Compile section (always visible)
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown('<div class="compile-card">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-label-green">📥 Compile Weekly Report</div>',
    unsafe_allow_html=True,
)

compile_fridays, compile_default_idx = get_fridays()

compile_col1, compile_col2 = st.columns([2, 1])

with compile_col1:
    compile_friday = st.selectbox(
        "Select week to compile",
        options=compile_fridays,
        index=compile_default_idx,
        format_func=lambda d: d.strftime("%b %d, %Y"),
        key="compile_week_select",
    )

# Show submission status for selected week
week_subs = {
    user: data
    for (user, friday), data in st.session_state.submissions.items()
    if friday == compile_friday
}

if week_subs:
    st.markdown(
        f'<div class="status-card">'
        f"📊 <strong>{len(week_subs)}</strong> submission(s) for this week: "
        f"<strong>{', '.join(sorted(week_subs.keys()))}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )
else:
    st.info("No submissions yet for this week.")

with compile_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    compile_clicked = st.button(
        "📥 Compile Selected Week",
        key="compile_btn",
        disabled=len(week_subs) == 0,
    )

if compile_clicked:
    csv_data = compile_week_csv(st.session_state.submissions, compile_friday, PROJECT_NAMES)
    if csv_data:
        st.session_state.compiled_csv = csv_data
        week_label = f"{compile_friday.month}_{compile_friday.day}"
        st.session_state.compiled_filename = f"work_planning_{week_label}.csv"
    else:
        st.warning("No submissions found for this week.")
        st.session_state.compiled_csv = None

if st.session_state.compiled_csv:
    st.download_button(
        label="⬇️ Download CSV",
        data=st.session_state.compiled_csv,
        file_name=st.session_state.compiled_filename,
        mime="text/csv",
        key="download_csv_btn",
    )

st.markdown("</div>", unsafe_allow_html=True)
