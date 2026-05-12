import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.vectorstore import get_chroma_vectorstore, load_config


def main() -> None:
    config = load_config("config.yaml")
    vs = get_chroma_vectorstore(config)

    query = "Quel est le chiffre d'affaires en 2023 ?"
    docs = vs.similarity_search(query, k=3)

    print(f"Query: {query!r}")
    print(f"Results: {len(docs)}\n")
    for i, d in enumerate(docs, start=1):
        meta = d.metadata
        preview = d.page_content[:220].replace("\n", " ")
        print(f"[{i}] file={meta.get('file_name')} type={meta.get('type')} section={meta.get('section')!r}")
        print(preview)
        print("----")


if __name__ == "__main__":
    main()
