"""Rebuild the Chroma vector store from everything in knowledge_base/.

Run this after adding or editing notebook entries or reference docs:
    python ingest.py
"""
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config

LOADERS_BY_SUFFIX = {
    ".md": TextLoader,
    ".txt": TextLoader,
    ".pdf": PyPDFLoader,
}


def load_documents():
    documents = []
    for source_dir, category in ((config.NOTEBOOK_DIR, "notebook"), (config.DOCS_DIR, "docs")):
        if not source_dir.exists():
            continue
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            loader_cls = LOADERS_BY_SUFFIX.get(path.suffix.lower())
            if loader_cls is None:
                continue
            loader = loader_cls(str(path))
            for doc in loader.load():
                doc.metadata["source"] = str(path.relative_to(config.KB_DIR))
                doc.metadata["category"] = category
                documents.append(doc)
    return documents


def build_index():
    documents = load_documents()
    if not documents:
        print(f"No documents found under {config.KB_DIR}. Add files to notebook/ or docs/ first.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model=config.EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)

    # Rebuild from scratch each run so edits/deletes in the knowledge base
    # aren't left behind as stale vectors. Clear contents rather than the
    # directory itself, since in Docker this path is a mounted volume and
    # its mount point can't be removed.
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    for child in config.CHROMA_DIR.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.CHROMA_DIR),
        # Cosine distance gives a better-calibrated [0, 1] relevance score
        # than Chroma's default (L2), which is what the web-search fallback
        # threshold relies on.
        collection_metadata={"hnsw:space": "cosine"},
    )
    print(f"Indexed {len(chunks)} chunks from {len(documents)} source files into {config.CHROMA_DIR}")


if __name__ == "__main__":
    build_index()
