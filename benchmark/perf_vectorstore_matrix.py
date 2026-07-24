import os
import sys
import statistics
import time
from typing import List, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.vectorstore import load_config, get_embeddings, get_or_create_faiss_vectorstore


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    k = int(round((len(vs) - 1) * p))
    k = max(0, min(len(vs) - 1, k))
    return vs[k]


def _ensure_file(path: str, target_chars: int) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        return
    line = "TechCorp est une entreprise fictive. Elle évolue sur un marché en croissance.\n"
    buf = []
    n = 0
    while n < target_chars:
        buf.append(line)
        n += len(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(buf)[:target_chars])


def _time_ms(fn, *args, **kwargs) -> float:
    t0 = time.perf_counter()
    fn(*args, **kwargs)
    return (time.perf_counter() - t0) * 1000.0


def _bench_case(
    *,
    file_path: str,
    doc_name: str,
    embeddings,
    config: Dict[str, Any],
    repeats_load: int,
    repeats_search: int,
) -> Dict[str, Any]:
    chunks = chunk_document(file_path)
    docs, _ = chunks_to_langchain_docs(chunks)

    build_ms = _time_ms(get_or_create_faiss_vectorstore, docs, doc_name, embeddings, config)

    load_times = []
    vectorstore = None
    for _ in range(max(1, repeats_load)):
        t = time.perf_counter()
        vectorstore = get_or_create_faiss_vectorstore([], doc_name, embeddings, config)
        load_times.append((time.perf_counter() - t) * 1000.0)

    search_times = []
    if vectorstore is not None:
        for _ in range(max(1, repeats_search)):
            t = time.perf_counter()
            vectorstore.similarity_search("marché", k=2)
            search_times.append((time.perf_counter() - t) * 1000.0)

    return {
        "docs": len(docs),
        "build_ms": build_ms,
        "load_ms_p50": _percentile(load_times, 0.50),
        "load_ms_p95": _percentile(load_times, 0.95),
        "search_ms_p50": _percentile(search_times, 0.50),
        "search_ms_p95": _percentile(search_times, 0.95),
    }


def main() -> None:
    config = load_config("config.yaml")
    t_emb0 = time.perf_counter()
    embeddings = get_embeddings(config)
    emb_ms = (time.perf_counter() - t_emb0) * 1000.0

    cases: List[Tuple[str, int]] = [
        ("small", 8_000),
        ("medium", 60_000),
        ("large", 220_000),
    ]

    print("embeddings_init_ms", round(emb_ms, 1))
    print("")
    print("case\tdocs\tbuild_ms\tload_p50\tload_p95\tsearch_p50\tsearch_p95")

    for name, size in cases:
        file_path = os.path.join("tmp", f"perf_{name}.txt")
        _ensure_file(file_path, size)
        doc_name = f"perf_{name}"
        res = _bench_case(
            file_path=file_path,
            doc_name=doc_name,
            embeddings=embeddings,
            config=config,
            repeats_load=5,
            repeats_search=20,
        )
        print(
            f"{name}\t{res['docs']}\t{round(res['build_ms'],1)}\t{round(res['load_ms_p50'],1)}\t{round(res['load_ms_p95'],1)}\t{round(res['search_ms_p50'],1)}\t{round(res['search_ms_p95'],1)}"
        )


if __name__ == "__main__":
    main()
