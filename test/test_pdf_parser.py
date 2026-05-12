import os

from agent.pdf_parser import parse_pdf


def main() -> None:
    sample = os.path.join(
        "data",
        "raw",
        "TotalEnergies",
        "fr",
        "2023",
        "totalenergies_document-enregistrement-universel-2023_2023_fr_pdf.pdf",
    )
    doc = parse_pdf(sample)
    pages = doc["pages"]
    print(f"Fichier: {doc['file_name']}")
    print(f"Pages (doc): {doc['page_count']}")
    print(f"Pages extraites: {len(pages)}")
    print()
    for p in pages[:3]:
        title = p["title"] or "-"
        section = p["section"] or "-"
        preview = (p["text"][:200] + "...") if len(p["text"]) > 200 else p["text"]
        print(f"p.{p['page']:>3} | title={title!r} | section={section!r}")
        print(preview)
        print("----")


if __name__ == "__main__":
    main()

