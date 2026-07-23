import subprocess
import sys
from datetime import datetime

import streamlit as st

import config
from rag.llm import answer_stream, simple_chat_stream
from rag.retrieval import retrieve_with_relevance
from rag.websearch import search_security_sources
from test_data.fixtures import FILE_FIXTURES, load_fixture_bytes
from test_data.prompts import ADVERSARIAL_PROMPTS
from vendors.registry import ALL_PROVIDERS

st.set_page_config(page_title="AI Threat Notebook", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of (role, content)

with st.sidebar:
    st.header("Web search fallback")
    web_search_enabled = st.toggle(
        "Search trusted security sites when the KB has no answer",
        value=config.WEB_SEARCH_ENABLED_DEFAULT,
    )
    force_web_search = st.checkbox("Always search the web too (even if KB matches)")
    with st.expander("Trusted sites"):
        for site in config.TRUSTED_SECURITY_SITES:
            st.markdown(f"- `{site}`")
        st.caption("Edit TRUSTED_SECURITY_SITES in config.py to change this list.")

chat_tab, kb_tab, live_test_tab = st.tabs(["Chat", "Knowledge Base / Notebook", "Live Vendor Test"])

# ---------------------------------------------------------------------------
# Chat tab
# ---------------------------------------------------------------------------
with chat_tab:
    st.title("AI Threat Notebook")
    st.caption(f"Model: {config.LLM_MODEL} · Embeddings: {config.EMBED_MODEL} · Store: Chroma (local)")

    if not config.CHROMA_DIR.exists():
        st.warning(
            "No knowledge base index found yet. Add notes/docs in the "
            "**Knowledge Base / Notebook** tab, then click **Rebuild index**."
        )

    for role, content in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(content)

    question = st.chat_input("Ask about AI security, agentic AI risks, or your own notes...")
    if question:
        st.session_state.messages.append(("user", question))
        with st.chat_message("user"):
            st.markdown(question)

        docs, best_score = retrieve_with_relevance(question)
        kb_has_answer = bool(docs) and best_score >= config.KB_RELEVANCE_THRESHOLD
        looks_time_sensitive = any(kw in question.lower() for kw in config.TIME_SENSITIVE_KEYWORDS)

        web_results = None
        if web_search_enabled and (force_web_search or not kb_has_answer or looks_time_sensitive):
            spinner_msg = (
                "Question looks time-sensitive — searching trusted security sites..."
                if looks_time_sensitive and kb_has_answer
                else "Knowledge base has no strong match — searching trusted security sites..."
            )
            with st.spinner(spinner_msg):
                web_results = search_security_sources(question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            partial = ""
            for chunk in answer_stream(question, st.session_state.messages[:-1], docs, web_results):
                partial += chunk
                placeholder.markdown(partial)

            if docs or web_results:
                with st.expander("Sources"):
                    if docs:
                        st.markdown("**From your knowledge base:**")
                        for s in sorted({d.metadata.get("source", "unknown") for d in docs}):
                            st.markdown(f"- `{s}`")
                    if web_results:
                        st.markdown("**From the web:**")
                        for r in web_results:
                            st.markdown(f"- [{r['title']}]({r['url']})")

        st.session_state.messages.append(("assistant", partial))

# ---------------------------------------------------------------------------
# Knowledge Base / Notebook tab
# ---------------------------------------------------------------------------
with kb_tab:
    st.header("Notebook")
    st.caption("Write down your own notes here. They're saved as markdown and become searchable after re-indexing.")

    existing_notes = sorted(config.NOTEBOOK_DIR.glob("*.md"))
    note_names = ["(new note)"] + [p.name for p in existing_notes]
    selected = st.selectbox("Select a note to edit, or start a new one", note_names)

    if selected == "(new note)":
        default_title = ""
        default_body = ""
    else:
        note_path = config.NOTEBOOK_DIR / selected
        default_title = selected.removesuffix(".md")
        default_body = note_path.read_text()

    title = st.text_input("Title (used as filename)", value=default_title)
    body = st.text_area("Note content (markdown)", value=default_body, height=300)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save note", disabled=not title.strip()):
            safe_name = "".join(c for c in title.strip() if c.isalnum() or c in (" ", "-", "_")).strip()
            safe_name = safe_name.replace(" ", "_") or f"note_{datetime.now():%Y%m%d_%H%M%S}"
            note_path = config.NOTEBOOK_DIR / f"{safe_name}.md"
            config.NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
            note_path.write_text(body)
            st.success(f"Saved {note_path.name}. Rebuild the index to make it searchable.")
            st.rerun()
    with col2:
        if selected != "(new note)" and st.button("Delete note"):
            (config.NOTEBOOK_DIR / selected).unlink()
            st.success(f"Deleted {selected}. Rebuild the index to remove it from search.")
            st.rerun()

    st.divider()
    st.header("Reference documents")
    st.caption("Drop in PDFs or markdown reference material for AI security / agentic AI security.")

    uploaded = st.file_uploader("Upload a document", type=["pdf", "md", "txt"])
    if uploaded is not None:
        config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        dest = config.DOCS_DIR / uploaded.name
        dest.write_bytes(uploaded.getvalue())
        st.success(f"Uploaded {uploaded.name}. Rebuild the index to make it searchable.")

    existing_docs = sorted(config.DOCS_DIR.glob("*")) if config.DOCS_DIR.exists() else []
    if existing_docs:
        st.markdown("**Current reference docs:**")
        for p in existing_docs:
            st.markdown(f"- `{p.name}`")

    st.divider()
    if st.button("Rebuild index", type="primary"):
        with st.spinner("Re-embedding knowledge base..."):
            result = subprocess.run(
                [sys.executable, str(config.ROOT_DIR / "ingest.py")],
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            st.success("Index rebuilt.")
            st.code(result.stdout)
        else:
            st.error("Indexing failed.")
            st.code(result.stderr)

# ---------------------------------------------------------------------------
# Live Vendor Test tab
# ---------------------------------------------------------------------------
with live_test_tab:
    st.title("Live Vendor Test")
    st.caption(
        "Mock guardrail vendors for local comparison - none of these call a real vendor API yet. "
        "Pick a vendor and a persona, run a test, then switch vendors and resend to compare."
    )

    if "live_test_log" not in st.session_state:
        st.session_state.live_test_log = []

    vendor_name = st.selectbox("Vendor", list(ALL_PROVIDERS.keys()))
    provider = ALL_PROVIDERS[vendor_name]
    persona = st.radio("Persona", ["External threat actor", "Insider threat"], horizontal=True)

    def render_verdict(verdict):
        renderer = {"allow": st.success, "flag": st.warning, "block": st.error}[verdict.outcome]
        renderer(f"**{verdict.vendor}** — {verdict.outcome.upper()}: {verdict.reason}")

    if persona == "External threat actor":

        def _apply_prompt_pick():
            picked = st.session_state.get("live_test_prompt_pick", "(custom)")
            st.session_state["live_test_prompt"] = (
                ""
                if picked == "(custom)"
                else next(p["text"] for p in ADVERSARIAL_PROMPTS if p["label"] == picked)
            )

        prompt_labels = ["(custom)"] + [p["label"] for p in ADVERSARIAL_PROMPTS]
        st.selectbox(
            "Sample adversarial prompt",
            prompt_labels,
            key="live_test_prompt_pick",
            on_change=_apply_prompt_pick,
        )
        # value= is intentionally omitted once "key" is set: Streamlit only honors
        # value on first render, so reactive updates must go through session_state
        # via the on_change callback above, not through this widget's own value=.
        prompt_text = st.text_area("Prompt to send", height=100, key="live_test_prompt")

        if st.button("Send", disabled=not prompt_text.strip()):
            st.markdown("**Prompt inspection**")
            prompt_verdict = provider.inspect_prompt(prompt_text)
            render_verdict(prompt_verdict)

            response_text, response_verdict = "", None
            if prompt_verdict.outcome != "block":
                st.markdown("**Model response**")
                placeholder = st.empty()
                partial = ""
                for chunk in simple_chat_stream(prompt_text, config.LIVE_TEST_SYSTEM_PROMPT):
                    partial += chunk
                    placeholder.markdown(partial)
                response_text = partial

                st.markdown("**Response inspection**")
                response_verdict = provider.inspect_response(response_text)
                render_verdict(response_verdict)
                if response_verdict.outcome == "block":
                    st.error("Response withheld by guardrail.")
            else:
                st.info("Blocked at the prompt stage - no request sent to the model.")

            st.session_state.live_test_log.append(
                {
                    "vendor": vendor_name,
                    "persona": persona,
                    "input": prompt_text,
                    "prompt_verdict": f"{prompt_verdict.outcome}: {prompt_verdict.reason}",
                    "response_verdict": f"{response_verdict.outcome}: {response_verdict.reason}" if response_verdict else "(not sent to model)",
                }
            )

    else:  # Insider threat
        fixture_labels = ["(upload custom file)"] + [f["label"] for f in FILE_FIXTURES]
        picked_fixture = st.selectbox("Sample sensitive file", fixture_labels)

        content_bytes, filename, content_type = None, None, None
        if picked_fixture == "(upload custom file)":
            uploaded = st.file_uploader("Upload a test file")
            if uploaded is not None:
                content_bytes = uploaded.getvalue()
                filename, content_type = uploaded.name, uploaded.type
        else:
            fixture = next(f for f in FILE_FIXTURES if f["label"] == picked_fixture)
            content_bytes = load_fixture_bytes(fixture["filename"])
            filename, content_type = fixture["filename"], fixture["content_type"]
            with st.expander(f"Preview {filename}"):
                st.code(content_bytes.decode("utf-8", errors="replace"))

        if content_bytes is not None and st.button("Inspect file"):
            st.markdown("**File inspection**")
            file_verdict = provider.inspect_file(filename, content_bytes, content_type or "")
            render_verdict(file_verdict)

            st.session_state.live_test_log.append(
                {
                    "vendor": vendor_name,
                    "persona": persona,
                    "input": filename,
                    "prompt_verdict": f"{file_verdict.outcome}: {file_verdict.reason}",
                    "response_verdict": "(n/a - file upload)",
                }
            )

    if st.session_state.live_test_log:
        st.divider()
        with st.expander(f"Comparison log ({len(st.session_state.live_test_log)} tests this session)"):
            st.dataframe(st.session_state.live_test_log, use_container_width=True)
            if st.button("Clear log"):
                st.session_state.live_test_log = []
                st.rerun()
