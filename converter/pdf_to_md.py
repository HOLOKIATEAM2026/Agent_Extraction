import pdfplumber
import fitz  # PyMuPDF

def pdf_to_markdown_with_tables(pdf_path: str) -> str:
    """
    Convert a PDF file to Markdown format, extracting tables and formatting them properly.
    Uses pdfplumber for table extraction and PyMuPDF (fitz) for text extraction with formatting.
    """
    md_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            md_parts.append(f"\n---\n<!-- page {page_num} -->\n")
            
            # Extract tables first
            tables = page.extract_tables()
            table_text = ""
            
            for table in tables:
                if not table:
                    continue
                # Convert table to Markdown
                header = table[0]
                md_table = "| " + " | ".join(str(h or "") for h in header) + " |\n"
                md_table += "| " + " | ".join(["---"] * len(header)) + " |\n"
                for row in table[1:]:
                    md_table += "| " + " | ".join(str(c or "") for c in row) + " |\n"
                table_text += md_table + "\n"
            
            # Extract normal text
            text = page.extract_text() or ""
            
            md_parts.append(text)
            if table_text:
                md_parts.append(table_text)
    
    return "\n".join(md_parts)
