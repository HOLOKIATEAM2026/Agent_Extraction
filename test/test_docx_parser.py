import os

from agent.docx_parser import parse_docx


def main() -> None:
    sample = os.path.join("specs_fonctionnelles.docx")
    doc = parse_docx(sample)
    blocks = doc["blocks"]
    print(f"Fichier: {doc['file_name']}")
    print(f"Blocks: {doc['block_count']}")
    print()
    for b in blocks[:12]:
        if b["type"] == "paragraph":
            print(
                f"[{b['index']}] PARA heading={b['is_heading']} style={b['style']!r} section={b['section']!r}"
            )
            print(b["text"][:240])
        else:
            rows = b["rows"]
            print(f"[{b['index']}] TABLE rows={len(rows)} section={b['section']!r}")
            if rows:
                print(" | ".join(rows[0])[:240])
        print("----")


if __name__ == "__main__":
    main()

