import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from math import log
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from bosquevivo.db.models import KbChunk

CORPUS = Path(__file__).parent / "corpus"
STOPWORDS = frozenset(
    [
        "a",
        "al",
        "algo",
        "como",
        "con",
        "cual",
        "cuando",
        "de",
        "del",
        "el",
        "ella",
        "en",
        "es",
        "esta",
        "este",
        "esto",
        "la",
        "las",
        "lo",
        "los",
        "me",
        "mi",
        "muy",
        "no",
        "o",
        "para",
        "pero",
        "por",
        "que",
        "se",
        "si",
        "sin",
        "son",
        "su",
        "sus",
        "un",
        "una",
        "uno",
        "y",
        "ya",
    ]
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    return [
        t for t in re.findall(r"[a-z0-9]+", normalize(text)) if t not in STOPWORDS and len(t) > 1
    ]


@dataclass(frozen=True)
class KnowledgeHit:
    chunk_id: int
    source: str
    title: str
    content: str
    score: float

    @property
    def citation(self) -> str:
        return f"{self.source} · {self.title}"


def split_markdown(source: str, text: str) -> list[tuple[str, str, str]]:
    chunks: list[tuple[str, str, str]] = []
    document_title = source
    current_title: str | None = None
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("# "):
            document_title = line[2:].strip()
        elif line.startswith("## "):
            if current_title and buffer:
                chunks.append((source, current_title, "\n".join(buffer).strip()))
            current_title = line[3:].strip()
            buffer = []
        else:
            buffer.append(line)
    if current_title and buffer:
        chunks.append((source, current_title, "\n".join(buffer).strip()))
    return [(f"{s} ({document_title})", t, c) for s, t, c in chunks if c]


class KnowledgeBase:
    def __init__(self, session: Session) -> None:
        self.session = session

    def load_directory(self, directory: Path = CORPUS) -> int:
        self.session.execute(delete(KbChunk))
        count = 0
        for path in sorted(directory.glob("*.md")):
            for source, title, content in split_markdown(
                path.stem, path.read_text(encoding="utf-8")
            ):
                self.session.add(KbChunk(source=source, title=title, content=content))
                count += 1
        self.session.flush()
        return count

    def search(self, query: str, limit: int = 3) -> list[KnowledgeHit]:
        chunks = self.session.scalars(select(KbChunk)).all()
        terms = tokenize(query)
        if not chunks or not terms:
            return []
        documents = [Counter(tokenize(f"{c.title} {c.title} {c.content}")) for c in chunks]
        total = len(documents)
        hits: list[KnowledgeHit] = []
        for chunk, counts in zip(chunks, documents, strict=True):
            score = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                containing = sum(1 for d in documents if term in d)
                score += (1 + log(frequency)) * (log((total + 1) / containing) + 1)
            if score > 0:
                hits.append(
                    KnowledgeHit(
                        chunk.id, chunk.source, chunk.title, chunk.content, round(score, 3)
                    )
                )
        return sorted(hits, key=lambda h: h.score, reverse=True)[:limit]
