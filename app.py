import subprocess
import sys
from datetime import datetime

import streamlit as st

import config
from rag.llm import answer_stream
from rag.retrieval import retrieve_with_relevance
from rag.websearch import search_security_sources

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

chat_tab, kb_tab = st.tabs(["Chat", "Knowledge Base / Notebook"])

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
