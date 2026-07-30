from __future__ import annotations

import re
import time
from pathlib import Path

import requests

from .config import CACHE_DIR
from .models import PageChunk


ARXIV_ID_PATTERN = re.compile(r"(?<!\d)(\d{4}\.\d{4,5}(?:v\d+)?)(?!\d)")


def parse_arxiv_id(value: str) -> str:
    match = ARXIV_ID_PATTERN.search(value or "")
    if not match:
        raise ValueError("No valid arXiv ID found")
    return match.group(1)


class ArxivPdfExtractor:
    def __init__(
        self,
        *,
        cache_dir: Path | None = None,
        session: requests.Session | None = None,
        timeout: int = 45,
    ) -> None:
        self.cache_dir = cache_dir or CACHE_DIR / "arxiv"
        self.session = session or requests.Session()
        self.timeout = timeout
        self.last_document_metadata: dict[str, int] = {}

    def download(self, arxiv_id_or_url: str) -> Path:
        arxiv_id = parse_arxiv_id(arxiv_id_or_url)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{arxiv_id}.pdf"
        if path.exists() and path.stat().st_size > 0:
            return path
        response = self.session.get(
            f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            headers={"User-Agent": "Paper2Venue-Hackathon/0.1"},
            timeout=self.timeout,
            stream=True,
        )
        response.raise_for_status()
        content_length = int(response.headers.get("content-length", "0") or 0)
        if content_length > 25 * 1024 * 1024:
            raise ValueError("PDF exceeds the 25 MB safety limit")
        with path.open("wb") as handle:
            written = 0
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                written += len(chunk)
                if written > 25 * 1024 * 1024:
                    handle.close()
                    path.unlink(missing_ok=True)
                    raise ValueError("PDF exceeds the 25 MB safety limit")
                handle.write(chunk)
        time.sleep(0.2)
        return path

    def extract(
        self,
        arxiv_id_or_url: str,
        *,
        max_pages: int = 12,
        max_chars: int = 60_000,
    ) -> list[PageChunk]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install pypdf: python -m pip install -r requirements.txt") from exc

        path = self.download(arxiv_id_or_url)
        reader = PdfReader(str(path))
        chunks: list[PageChunk] = []
        remaining = max(2_000, min(int(max_chars), 600_000))
        for page_number, page in enumerate(reader.pages[: max(1, int(max_pages))], start=1):
            if remaining <= 0:
                break
            raw_text = page.extract_text() or ""
            text = "\n".join(
                " ".join(line.split())
                for line in raw_text.splitlines()
                if line.strip()
            )
            if not text:
                continue
            text = text[:remaining]
            chunks.append(PageChunk(page=page_number, text=text))
            remaining -= len(text)
        self.last_document_metadata = {
            "total_pages": len(reader.pages),
            "extracted_pages": len(chunks),
            "extracted_characters": sum(len(chunk.text) for chunk in chunks),
        }
        return chunks
