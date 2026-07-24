import os
import time

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.vectorstore import load_config, get_embeddings, get_or_create_faiss_vectorstore


def main():
    file_path = os.path.join("tmp", "small.txt")
    if not os.path.exists(file_path):
        raise SystemExit("Missing tmp/small.txt")

    config = load_config("config.yaml")
    t_emb0 = time.perf_counter()
    embeddings = get_embeddings(config)
    emb_ms = (time.perf_counter() - t_emb0) * 1000.0

    chunks = chunk_document(file_path)
    docs, _ = chunks_to_langchain_docs(chunks)
    doc_name = os.path.basename(file_path).split(".")[0]

    t_build0 = time.perf_counter()
    get_or_create_faiss_vectorstore(docs, doc_name, embeddings=embeddings, config=config)
    build_ms = (time.perf_counter() - t_build0) * 1000.0

    t_load0 = time.perf_counter()
    get_or_create_faiss_vectorstore([], doc_name, embeddings=embeddings, config=config)
    load_ms = (time.perf_counter() - t_load0) * 1000.0

    print("embeddings_init_ms", round(emb_ms, 1))
    print("faiss_build_ms", round(build_ms, 1), "docs", len(docs))
    print("faiss_load_ms", round(load_ms, 1))


if __name__ == "__main__":
    main()

