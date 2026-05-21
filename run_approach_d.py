import argparse
import os

from benchmark.approach_d_combo import run_approach_d, save_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Chemin vers .pdf/.docx/.txt")
    parser.add_argument("--provider", default=None, help="groq | ollama | openai | gemini")
    parser.add_argument("--model", default=None, help="Nom du modèle (optionnel)")
    parser.add_argument("--config", default="config.yaml", help="Chemin config.yaml")
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--max-chunks", type=int, default=10)
    parser.add_argument("--max-chars-per-doc", type=int, default=600)
    parser.add_argument("--max-llm-context-chars", type=int, default=8000)
    parser.add_argument("--fix-passes", type=int, default=1)
    parser.add_argument("--out", default=None, help="Chemin de sortie .json")
    args = parser.parse_args()

    result = run_approach_d(
        args.input,
        provider=args.provider,
        model=args.model,
        config_path=args.config,
        top_k_per_query=args.top_k,
        max_chunks_total=args.max_chunks,
        max_chars_per_doc=args.max_chars_per_doc,
        max_llm_context_chars=args.max_llm_context_chars,
        max_fix_passes=args.fix_passes,
    )

    out_path = args.out
    if not out_path:
        base = os.path.basename(args.input)
        safe = "".join([c for c in base if c.isalnum() or c in "._-"]).strip(".")
        out_path = os.path.join("benchmark", "out", f"{safe}.approach_d.json")

    save_result(result, out_path)
    print(out_path)


if __name__ == "__main__":
    main()

