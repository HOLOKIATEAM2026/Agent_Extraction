import argparse
import os

from benchmark.approach_c_agent import run_approach_c, save_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Chemin vers .pdf/.docx/.txt")
    parser.add_argument("--provider", default=None, help="groq | ollama | openai | gemini")
    parser.add_argument("--model", default=None, help="Nom du modèle (optionnel)")
    parser.add_argument("--config", default="config.yaml", help="Chemin config.yaml")
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--out", default=None, help="Chemin de sortie .json")
    args = parser.parse_args()

    result = run_approach_c(
        args.input,
        provider=args.provider,
        model=args.model,
        config_path=args.config,
        max_steps=args.steps,
        top_k=args.top_k,
    )

    out_path = args.out
    if not out_path:
        base = os.path.basename(args.input)
        safe = "".join([c for c in base if c.isalnum() or c in "._-"]).strip(".")
        out_path = os.path.join("benchmark", "out", f"{safe}.approach_c.json")

    save_result(result, out_path)
    print(out_path)


if __name__ == "__main__":
    main()
