"""Section chunking that repeats the original heading on every child chunk."""
import re

from .chunking import RecursiveChunker


class HeadingChunker:
    def __init__(self, chunk_size: int = 500):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []
        chunks = []
        for section in re.split(r"(?m)(?=^#{1,6} )", text):
            section = section.strip()
            if not section:
                continue
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue
            heading, _, body = section.partition("\n")
            if heading.startswith("#"):
                prefix = heading + "\n"
                available = self.chunk_size - len(prefix)
                if available <= 0:
                    raise ValueError("chunk_size must leave room for heading and content")
                chunks.extend(prefix + part for part in RecursiveChunker(chunk_size=available).chunk(body))
            else:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(section))
        return chunks
