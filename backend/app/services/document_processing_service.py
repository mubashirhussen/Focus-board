import os
import re
import math
import json
import zipfile
import html
from typing import List, Dict, Any, Optional, Tuple

class DocumentChunkDTO:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        heading: Optional[str] = None,
        page_number: Optional[int] = None,
        token_count: int = 0,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_index = chunk_index
        self.content = content
        self.heading = heading
        self.page_number = page_number
        self.token_count = token_count
        self.embedding = embedding or []
        self.metadata = metadata or {}

class DocumentProcessingService:
    EMBEDDING_DIM = 128

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str, mime_type: Optional[str] = None) -> str:
        """Extract plain text from uploaded document bytes across various formats."""
        ext = os.path.splitext(filename)[1].lower() if filename else ""

        # 1. Plain text / Markdown / RST
        if ext in [".txt", ".md", ".markdown", ".rst", ".log", ".yaml", ".yml"] or (mime_type and "text/" in mime_type):
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="ignore")

        # 2. JSON
        if ext == ".json" or (mime_type and "application/json" in mime_type):
            try:
                data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
                return json.dumps(data, indent=2)
            except Exception:
                return file_bytes.decode("utf-8", errors="ignore")

        # 3. CSV
        if ext == ".csv" or (mime_type and "text/csv" in mime_type):
            try:
                lines = file_bytes.decode("utf-8", errors="ignore").splitlines()
                if not lines:
                    return ""
                headers = [h.strip() for h in lines[0].split(",")]
                extracted = [f"Columns: {', '.join(headers)}"]
                for i, row in enumerate(lines[1:500]):
                    vals = [v.strip() for v in row.split(",")]
                    pairs = [f"{h}: {v}" for h, v in zip(headers, vals) if v]
                    if pairs:
                        extracted.append(f"Row {i+1}: {', '.join(pairs)}")
                return "\n".join(extracted)
            except Exception:
                return file_bytes.decode("utf-8", errors="ignore")

        # 4. HTML
        if ext in [".html", ".htm"] or (mime_type and "text/html" in mime_type):
            raw = file_bytes.decode("utf-8", errors="ignore")
            # Strip scripts and styles
            raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            # Replace tags with spaces
            raw = re.sub(r"<[^>]+>", " ", raw)
            return html.unescape(re.sub(r"\s+", " ", raw).strip())

        # 5. DOCX (OpenXML)
        if ext == ".docx":
            try:
                import io
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx:
                    xml_content = docx.read("word/document.xml").decode("utf-8")
                    # Extract text inside <w:t> tags
                    paragraphs = []
                    for p in re.findall(r"<w:p[^>]*>(.*?)</w:p>", xml_content, flags=re.DOTALL):
                        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", p)
                        if texts:
                            paragraphs.append("".join(texts))
                    return "\n\n".join(paragraphs)
            except Exception:
                pass

        # 6. PDF
        if ext == ".pdf" or (mime_type and "application/pdf" in mime_type):
            try:
                import io
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                    return "\n\n".join(pages)
                except ImportError:
                    pass

                # Fallback PDF stream extraction
                content = file_bytes.decode("latin-1", errors="ignore")
                text_chunks = re.findall(r"\((.*?)\)\s*Tj", content)
                if text_chunks:
                    return " ".join(text_chunks)
            except Exception:
                pass

        # Generic fallback
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return str(file_bytes)

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate token count (approximately 4 chars per token)."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    @classmethod
    def chunk_document(
        cls,
        text: str,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunkDTO]:
        """Split text into overlapping chunks, tracking section headings and generating embeddings."""
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        lines = clean_text.splitlines()

        chunks: List[DocumentChunkDTO] = []
        current_heading = "Overview"
        current_page = 1

        # Break text by paragraphs or headings first
        blocks: List[Tuple[str, str, int]] = []  # (content, heading, page)
        curr_block = []

        for line in lines:
            stripped = line.strip()
            # Detect Markdown headings
            if stripped.startswith("#"):
                heading_text = stripped.lstrip("#").strip()
                if curr_block:
                    blocks.append(("\n".join(curr_block), current_heading, current_page))
                    curr_block = []
                current_heading = heading_text
                curr_block.append(stripped)
            elif "--- Page " in stripped or "=== Page " in stripped:
                match = re.search(r"Page\s+(\d+)", stripped)
                if match:
                    current_page = int(match.group(1))
            else:
                curr_block.append(line)

        if curr_block:
            blocks.append(("\n".join(curr_block), current_heading, current_page))

        # Now group blocks into size-bounded chunks with overlap
        chunk_index = 0
        current_chunk_text = ""
        active_heading = current_heading
        active_page = 1

        for blk_text, blk_heading, blk_page in blocks:
            if not blk_text.strip():
                continue

            # If block itself is larger than chunk_size, slice it
            if len(blk_text) > chunk_size:
                start = 0
                while start < len(blk_text):
                    end = min(len(blk_text), start + chunk_size)
                    sub_text = blk_text[start:end].strip()
                    if sub_text:
                        emb = cls.generate_embedding(sub_text)
                        chunks.append(
                            DocumentChunkDTO(
                                chunk_index=chunk_index,
                                content=sub_text,
                                heading=blk_heading,
                                page_number=blk_page,
                                token_count=cls.estimate_tokens(sub_text),
                                embedding=emb,
                                metadata={"length": len(sub_text), **(metadata or {})},
                            )
                        )
                        chunk_index += 1
                    start += (chunk_size - chunk_overlap)
                continue

            # Check if adding this block exceeds chunk_size
            if len(current_chunk_text) + len(blk_text) + 2 > chunk_size and current_chunk_text.strip():
                emb = cls.generate_embedding(current_chunk_text)
                chunks.append(
                    DocumentChunkDTO(
                        chunk_index=chunk_index,
                        content=current_chunk_text.strip(),
                        heading=active_heading,
                        page_number=active_page,
                        token_count=cls.estimate_tokens(current_chunk_text),
                        embedding=emb,
                        metadata={"length": len(current_chunk_text), **(metadata or {})},
                    )
                )
                chunk_index += 1

                # Carry over overlap
                overlap_text = current_chunk_text[-chunk_overlap:] if len(current_chunk_text) > chunk_overlap else ""
                current_chunk_text = overlap_text + "\n" + blk_text
                active_heading = blk_heading
                active_page = blk_page
            else:
                if current_chunk_text:
                    current_chunk_text += "\n" + blk_text
                else:
                    current_chunk_text = blk_text
                    active_heading = blk_heading
                    active_page = blk_page

        # Final chunk
        if current_chunk_text.strip():
            emb = cls.generate_embedding(current_chunk_text)
            chunks.append(
                DocumentChunkDTO(
                    chunk_index=chunk_index,
                    content=current_chunk_text.strip(),
                    heading=active_heading,
                    page_number=active_page,
                    token_count=cls.estimate_tokens(current_chunk_text),
                    embedding=emb,
                    metadata={"length": len(current_chunk_text), **(metadata or {})},
                )
            )

        return chunks

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """Generate a deterministic 128-dimensional unit-normalized embedding vector.
        Uses subword hashing and term frequency mapping with cosine normalization.
        """
        if not text:
            return [0.0] * cls.EMBEDDING_DIM

        vec = [0.0] * cls.EMBEDDING_DIM
        words = re.findall(r"[A-Za-z0-9_]+", text.lower())

        for w in words:
            # Word hashing
            h = hash(w) % cls.EMBEDDING_DIM
            vec[h] += 1.0

            # Character 3-grams for subword morphological capture
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    sub = w[i:i+3]
                    sub_h = hash(sub) % cls.EMBEDDING_DIM
                    vec[sub_h] += 0.5

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            vec = [round(v / norm, 6) for v in vec]
        return vec

    @classmethod
    def cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two unit vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        return max(0.0, min(1.0, dot))

    @classmethod
    def extract_summary(cls, text: str, max_sentences: int = 3) -> Dict[str, Any]:
        """Generate structured document summary and key takeaways."""
        if not text or not text.strip():
            return {
                "summary": "Document is empty.",
                "key_points": [],
            }

        sentences = [s.strip() for s in re.split(r"[.\n]+", text) if len(s.strip()) > 20]
        if not sentences:
            sentences = [text.strip()[:200]]

        # Pick key sentences (prioritizing headings and decision statements)
        key_sentences = []
        for s in sentences:
            lower = s.lower()
            if any(k in lower for k in ["decid", "decision", "require", "purpose", "architecture", "goal", "standard", "implement"]):
                key_sentences.append(s)
            if len(key_sentences) >= max_sentences:
                break

        if len(key_sentences) < max_sentences:
            for s in sentences:
                if s not in key_sentences:
                    key_sentences.append(s)
                if len(key_sentences) >= max_sentences:
                    break

        summary_text = " ".join(key_sentences[:max_sentences])
        key_points = [f"• {s}" for s in key_sentences[:max_sentences]]

        return {
            "summary": summary_text,
            "key_points": key_points,
        }
