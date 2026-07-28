import os
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from agent.pdf_parser import parse_pdf
from agent.docx_parser import parse_docx


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _join_with_separators(parts: Sequence[str]) -> str:
    return "\n\n".join([p for p in parts if p])


def _split_text(text: str, *, max_chars: int, overlap_chars: int) -> List[str]:
    if max_chars <= 0:
        return [text]
    if overlap_chars < 0:
        overlap_chars = 0
    if overlap_chars >= max_chars:
        overlap_chars = max_chars // 5

    t = text or ""
    if len(t) <= max_chars:
        return [t]

    out: List[str] = []
    start = 0
    step = max_chars - overlap_chars if (max_chars - overlap_chars) > 0 else max_chars
    while start < len(t):
        end = min(len(t), start + max_chars)
        out.append(t[start:end])
        if end >= len(t):
            break
        start = start + step
    return out


def _group_contiguous_by_section(
    pieces: Sequence[Tuple[Dict[str, Any], str]],
) -> List[Tuple[Optional[str], List[Tuple[Dict[str, Any], str]]]]:
    groups: List[Tuple[Optional[str], List[Tuple[Dict[str, Any], str]]]] = []
    cur: List[Tuple[Dict[str, Any], str]] = []
    cur_section: Optional[str] = None

    for meta, text in pieces:
        section = meta.get("section")
        if cur and section != cur_section:
            groups.append((cur_section, cur))
            cur = []
        cur_section = section
        cur.append((meta, text))

    if cur:
        groups.append((cur_section, cur))
    return groups


def chunk_pieces(
    pieces: Sequence[Tuple[Dict[str, Any], str]],
    *,
    max_chars: int = 6000,
    overlap_chars: int = 600,
) -> List[Dict[str, Any]]:
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be >= 0")
    if overlap_chars >= max_chars:
        overlap_chars = max_chars // 5

    chunks: List[Dict[str, Any]] = []
    i = 0
    while i < len(pieces):
        cur_parts: List[str] = []
        cur_meta: List[Dict[str, Any]] = []
        cur_len = 0

        j = i
        while j < len(pieces):
            meta, text = pieces[j]
            if not text:
                j += 1
                continue
            add_len = len(text) + (2 if cur_parts else 0)
            if cur_parts and (cur_len + add_len) > max_chars:
                break
            cur_parts.append(text)
            cur_meta.append(meta)
            cur_len += add_len
            j += 1

        if not cur_parts:
            meta, text = pieces[i]
            chunks.append({"meta": [meta], "text": text[:max_chars]})
            i += 1
            continue

        chunks.append({"meta": cur_meta, "text": _join_with_separators(cur_parts)})

        if j >= len(pieces):
            break

        if overlap_chars <= 0:
            i = j
            continue

        chunk_size = j - i
        if chunk_size <= 1:
            i = j
            continue

        overlap_len = 0
        overlap_count = 0
        k = len(cur_parts) - 1
        while k >= 1:
            text_k = cur_parts[k]
            overlap_len += len(text_k) + (2 if overlap_count else 0)
            overlap_count += 1
            if overlap_len >= overlap_chars:
                break
            k -= 1

        if overlap_count <= 0:
            i = j
        else:
            i = j - overlap_count

    return chunks


def chunk_pdf(
    file_path: str,
    *,
    max_chars: int = 6000,
    overlap_chars: int = 600,
) -> List[Dict[str, Any]]:
    doc = parse_pdf(file_path)
    pages = doc["pages"]

    pieces: List[Tuple[Dict[str, Any], str]] = []
    for p in pages:
        page_num = p["page"]
        section = p.get("section")
        title = p.get("title")
        text = p.get("text") or ""
        if not text:
            continue
        prefix = f"Page {page_num}\n"
        payload = prefix + text
        parts = _split_text(payload, max_chars=max_chars, overlap_chars=overlap_chars)
        for part_i, part in enumerate(parts):
            meta = {
                "page": page_num,
                "section": section,
                "title": title,
                "part": part_i + 1,
                "part_total": len(parts),
            }
            pieces.append((meta, part))

    out: List[Dict[str, Any]] = []
    for section_key, group in _group_contiguous_by_section(pieces):
        raw_chunks = chunk_pieces(group, max_chars=max_chars, overlap_chars=overlap_chars)
        for c in raw_chunks:
            metas = c["meta"]
            pages_in_chunk = sorted({m.get("page") for m in metas if m.get("page") is not None})

            titles = [m.get("title") for m in metas if m.get("title")]
            title = titles[0] if titles else None

            out.append(
                {
                    "id": _new_id("pdf"),
                    "type": "pdf",
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "section": section_key,
                    "title": title,
                    "pages": pages_in_chunk,
                    "text": c["text"],
                }
            )
    return out


def chunk_docx(
    file_path: str,
    *,
    max_chars: int = 6000,
    overlap_chars: int = 600,
) -> List[Dict[str, Any]]:
    doc = parse_docx(file_path)
    blocks = doc["blocks"]

    pieces: List[Tuple[Dict[str, Any], str]] = []
    for b in blocks:
        if b["type"] == "paragraph":
            text = b.get("text") or ""
            if not text:
                continue
            parts = _split_text(text, max_chars=max_chars, overlap_chars=overlap_chars)
            for part_i, part in enumerate(parts):
                meta = {
                    "block_index": b.get("index"),
                    "section": b.get("section"),
                    "is_heading": b.get("is_heading"),
                    "style": b.get("style"),
                    "part": part_i + 1,
                    "part_total": len(parts),
                }
                pieces.append((meta, part))
        elif b["type"] == "table":
            rows = b.get("rows") or []
            if not rows:
                continue
            flat_lines: List[str] = []
            for row in rows:
                flat_lines.append(" | ".join([c for c in row if c]))
            table_text = _join_with_separators(flat_lines)
            parts = _split_text(table_text, max_chars=max_chars, overlap_chars=overlap_chars)
            for part_i, part in enumerate(parts):
                meta = {
                    "block_index": b.get("index"),
                    "section": b.get("section"),
                    "table_index": b.get("table_index"),
                    "part": part_i + 1,
                    "part_total": len(parts),
                }
                pieces.append((meta, part))

    out: List[Dict[str, Any]] = []
    for section_key, group in _group_contiguous_by_section(pieces):
        raw_chunks = chunk_pieces(group, max_chars=max_chars, overlap_chars=overlap_chars)
        for c in raw_chunks:
            metas = c["meta"]
            block_indexes = sorted(
                {m.get("block_index") for m in metas if m.get("block_index") is not None}
            )

            out.append(
                {
                    "id": _new_id("docx"),
                    "type": "docx",
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "section": section_key,
                    "block_indexes": block_indexes,
                    "text": c["text"],
                }
            )
    return out


def chunk_document(
    file_path: str,
    *,
    max_chars: int = 6000,
    overlap_chars: int = 600,
) -> List[Dict[str, Any]]:
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        return chunk_pdf(file_path, max_chars=max_chars, overlap_chars=overlap_chars)
    if lower.endswith(".docx"):
        return chunk_docx(file_path, max_chars=max_chars, overlap_chars=overlap_chars)
    if lower.endswith(".txt") or lower.endswith(".md"):
        return chunk_txt(file_path, max_chars=max_chars, overlap_chars=overlap_chars)
    raise ValueError("Unsupported document type (expected .pdf, .docx, .txt or .md)")


def _split_text_with_indices(text: str, *, max_chars: int, overlap_chars: int):
    if max_chars <= 0:
        return [(0, len(text or ""), text or "")]
    if overlap_chars < 0:
        overlap_chars = 0
    if overlap_chars >= max_chars:
        overlap_chars = max_chars // 5

    t = text or ""
    if len(t) <= max_chars:
        return [(0, len(t), t)]

    out = []
    start = 0
    step = max_chars - overlap_chars if (max_chars - overlap_chars) > 0 else max_chars
    while start < len(t):
        end = min(len(t), start + max_chars)
        out.append((start, end, t[start:end]))
        if end >= len(t):
            break
        start = start + step
    return out


def chunk_txt(
    file_path: str,
    *,
    max_chars: int = 6000,
    overlap_chars: int = 600,
) -> List[Dict[str, Any]]:
    import re
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    page_matches = list(re.finditer(r"(?:<!-- page (\d+) -->|\[PAGE\s+(\d+)\])", raw, re.IGNORECASE))
    
    if page_matches:
        splits = []
        prev_pos = 0
        prev_page = 1
        for m in page_matches:
            p = int(m.group(1) or m.group(2))
            start_content = m.end()
            if m.start() > prev_pos or len(splits) == 0:
                splits.append((prev_page, prev_pos, m.start()))
            prev_page = p
            prev_pos = start_content
        splits.append((prev_page, prev_pos, len(raw)))

        out: List[Dict[str, Any]] = []
        for page_num, start, end in splits:
            seg_text = raw[start:end].strip()
            if not seg_text:
                continue

            seg_parts = _split_text_with_indices(seg_text, max_chars=max_chars, overlap_chars=overlap_chars)
            for _part_i, (_, _, part_txt) in enumerate(seg_parts):
                clean = part_txt.strip()
                if not clean:
                    continue
                pages_list = [page_num]
                chunk_dict = {
                    "id": _new_id("txt"),
                    "type": "txt",
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "section": None,
                    "pages": pages_list,
                    "page": page_num,
                    "text": clean,
                }
                out.append(chunk_dict)
        return out

    pieces: List[Tuple[Dict[str, Any], str]] = []
    parts_with_idx = _split_text_with_indices(raw, max_chars=max_chars, overlap_chars=overlap_chars)
    for part_i, (_, _, part) in enumerate(parts_with_idx):
        meta = {"section": None, "part": part_i + 1, "part_total": len(parts_with_idx)}
        pieces.append((meta, part.strip()))

    raw_chunks = chunk_pieces(pieces, max_chars=max_chars, overlap_chars=overlap_chars)
    out: List[Dict[str, Any]] = []
    for c in raw_chunks:
        metas = c["meta"]
        parts_idx = sorted({m.get("part") for m in metas if m.get("part") is not None})
        
        pages = []
        for m in metas:
            if m.get("pages"):
                pages.extend(m.get("pages"))
        pages = sorted(list(set(pages)))
        
        chunk_dict = {
            "id": _new_id("txt"),
            "type": "txt",
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "section": None,
            "parts": parts_idx,
            "text": c["text"],
        }
        
        if pages:
            chunk_dict["pages"] = pages
            chunk_dict["page"] = pages[0]
            
        out.append(chunk_dict)

    return out
