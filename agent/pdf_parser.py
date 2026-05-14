import os
import re
from typing import Any, Dict, List, Optional, Tuple

import fitz


def _clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    n = len(values)
    mid = n // 2
    if n % 2 == 1:
        return float(values[mid])
    return float(values[mid - 1] + values[mid]) / 2.0


def _merge_spans_to_lines(spans: List[Dict[str, Any]]) -> List[Tuple[float, str]]:
    spans = sorted(spans, key=lambda s: (s["y0"], s["x0"]))
    lines: List[Tuple[float, List[str]]] = []
    for s in spans:
        y0 = float(s["y0"])
        t = str(s["text"]).strip()
        if not t:
            continue
        if not lines:
            lines.append((y0, [t]))
            continue
        last_y0, parts = lines[-1]
        if abs(y0 - last_y0) <= 2.0:
            parts.append(t)
        else:
            lines.append((y0, [t]))
    return [(y0, _clean_text(" ".join(parts))) for y0, parts in lines]


def _extract_heading_candidates(page: fitz.Page) -> List[str]:
    d = page.get_text("dict")
    sizes: List[float] = []
    raw_spans: List[Dict[str, Any]] = []

    for block in d.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = str(span.get("text", "")).strip()
                if not text:
                    continue
                size = float(span.get("size", 0.0))
                bbox = span.get("bbox", [0, 0, 0, 0])
                sizes.append(size)
                raw_spans.append(
                    {
                        "text": text,
                        "size": size,
                        "x0": float(bbox[0]),
                        "y0": float(bbox[1]),
                    }
                )

    med = _median(sizes)
    threshold = max(12.0, med + 2.0)

    candidates = [
        s
        for s in raw_spans
        if s["size"] >= threshold and 2 <= len(s["text"]) <= 120
    ]

    lines = _merge_spans_to_lines(candidates)
    headings: List[str] = []
    seen = set()
    for _, line in lines:
        if not line:
            continue
        if line.lower().startswith(("page ", "table ", "figure ")):
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        headings.append(line)
        if len(headings) >= 3:
            break
    return headings


def parse_pdf(
    file_path: str,
    *,
    keep_empty_pages: bool = False,
) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    doc = fitz.open(file_path)
    try:
        pages: List[Dict[str, Any]] = []
        current_section: Optional[str] = None

        for i in range(doc.page_count):
            page = doc.load_page(i)
            text = _clean_text(page.get_text("text"))
            headings = _extract_heading_candidates(page)

            page_title = headings[0] if headings else None
            if page_title:
                current_section = page_title

            if not keep_empty_pages and not text:
                continue

            pages.append(
                {
                    "page": i + 1,
                    "title": page_title,
                    "section": current_section,
                    "headings": headings,
                    "text": text,
                }
            )

        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "page_count": doc.page_count,
            "pages": pages,
        }
    finally:
        doc.close()

