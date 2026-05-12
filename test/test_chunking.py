import os

from agent.chunking import chunk_document


def _print_summary(chunks, label: str) -> None:
    print(f"=== {label} ===")
    print(f"chunks: {len(chunks)}")
    if not chunks:
        return
    first = chunks[0]
    print(f"first.id: {first['id']}")
    print(f"first.section: {first.get('section')!r}")
    if first["type"] == "pdf":
        print(f"first.pages: {first.get('pages')[:10]}")
    else:
        print(f"first.block_indexes: {first.get('block_indexes')[:10]}")
    print(f"first.text_preview: {first['text'][:220].replace(chr(10), ' ') }")
    print()


def main() -> None:
    pdf_path = os.path.join(
        "data",
        "raw",
        "TotalEnergies",
        "fr",
        "2023",
        "totalenergies_document-enregistrement-universel-2023_2023_fr_pdf.pdf",
    )
    docx_path = "specs_fonctionnelles.docx"

    pdf_chunks = chunk_document(pdf_path, max_chars=6000, overlap_chars=600)
    docx_chunks = chunk_document(docx_path, max_chars=6000, overlap_chars=600)

    _print_summary(pdf_chunks, "PDF")
    _print_summary(docx_chunks, "DOCX")


if __name__ == "__main__":
    main()

