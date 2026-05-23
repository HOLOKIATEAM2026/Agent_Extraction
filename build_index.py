import argparse

from agent.indexing import build_chroma_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Chroma vector index from data/raw")
    parser.add_argument("--reset", action="store_true", help="Reset (delete) existing index before building")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Directory containing documents to index")
    parser.add_argument("--limit-files", type=int, default=None, help="Limit number of files to index")
    parser.add_argument("--max-chars", type=int, default=2000, help="Max characters per chunk")
    parser.add_argument("--overlap-chars", type=int, default=200, help="Overlap characters between chunks")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for vectorstore inserts")
    parser.add_argument("--max-chunks-per-file", type=int, default=300, help="Limit number of chunks per file (avoid huge EDGAR files)")
    parser.add_argument("--supabase", action="store_true", help="Upsert document metadata into Supabase during indexing")
    args = parser.parse_args()

    result = build_chroma_index(
        data_dir=args.data_dir,
        reset=args.reset,
        limit_files=args.limit_files,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
        batch_size=args.batch_size,
        max_chunks_per_file=args.max_chunks_per_file,
        enable_supabase=args.supabase,
    )

    print("\n✅ Indexation terminée")
    for k, v in result.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
