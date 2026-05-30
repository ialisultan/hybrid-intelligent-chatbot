"""Load and chunk documents from the data directory."""

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_chunk_documents(
    data_dir: str = "data",
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """Load markdown/text files and split into chunks for indexing."""
    path = Path(data_dir)
    if not path.exists():
        return []

    raw_docs: list[Document] = []
    for pattern in ("**/*.md", "**/*.txt"):
        loader = DirectoryLoader(
            str(path),
            glob=pattern,
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=False,
            silent_errors=True,
        )
        raw_docs.extend(loader.load())
    if not raw_docs:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(raw_docs)

    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        chunk.metadata["source"] = Path(source).name

    return chunks
