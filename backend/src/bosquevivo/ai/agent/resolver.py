import math
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.db.models import Project

_FUNCTION_WORDS = (
    "a al algo ante aqui asi aun cada como con contra cual cuales cuando cuanto cuantos cuantas "
    "de del desde donde dos e el ella ellos en entre era eres es esa ese eso esta estan estar "
    "este esto fue ha hace hay hasta la las le les lo los me mi mis mas menos muy ni no nos o "
    "otro para pero por porque que quien quienes se ser si sin sobre son su sus te ti tu tus "
    "u un una uno unos unas va vamos van voy y ya yo cuentame dime quiero quisiera saber favor "
    "the of and for in on departamento department municipio municipality ubicacion ubicado "
    "ubicada ubicados queda quedan region vereda zona territorio pais country location"
)
FUNCTION_WORDS = frozenset(_FUNCTION_WORDS.split())

_PLACE_WORDS = (
    "amazonas amazonia andina antioquia arauca atlantico bolivar boyaca caldas caqueta caribe "
    "casanare cauca cesar choco colombia cordoba cundinamarca darien guainia guaviare huila "
    "guajira magdalena meta narino orinoquia pacifico putumayo quindio risaralda santander sucre "
    "tolima valle vaupes vichada"
)
PLACE_WORDS = frozenset(_PLACE_WORDS.split())

_DOMAIN_WORDS = (
    "bosque bosques proyecto proyectos project projects finca fincas indice puntaje estado "
    "alerta alertas permanencia satelite satelital hectarea hectareas carbono carbon forestal "
    "forest conservacion conservation reforestacion reforestation restauracion restoration "
    "deforestacion perdida tala confianza credibilidad metodologia imagen imagenes foto fotos "
    "grouped program programa pasa pasando ocurre ocurrio informacion resumen"
)
DOMAIN_WORDS = frozenset(_DOMAIN_WORDS.split())

DISTINCT_COVERAGE = 0.5
COMPLETE_COVERAGE = 0.95
MARGIN = 1.0
UNMATCHED_PENALTY = 0.15
COMMON_SHARE = 0.15
MIN_COMMON_FREQUENCY = 3
FUZZY_RATIO = 82
FUZZY_MIN_LENGTH = 5
ID_TOKEN_LENGTH = 5
SHORT_QUERY_TOKENS = 3
SHORT_QUERY_FREQUENCY = 4
SHORT_QUERY_LENGTH = 6
MAX_CANDIDATES = 4
EXPLICIT_ID = re.compile(r"\b(?:proyecto|id|numero)\s*#?\s*(\d{1,7})\b")


def normalize(text: str) -> str:
    folded = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def message_tokens(text: str) -> list[str]:
    tokens = normalize(text).split()
    return [t for t in tokens if len(t) > 1 and not t.isdigit() and t not in FUNCTION_WORDS]


def name_tokens(name: str) -> list[str]:
    tokens = message_tokens(name)
    distinctive = [t for t in tokens if t not in DOMAIN_WORDS]
    return distinctive or tokens


def tokens_match(typed: str, known: str) -> bool:
    if typed == known:
        return True
    if len(known) < FUZZY_MIN_LENGTH or len(typed) < FUZZY_MIN_LENGTH - 1:
        return False
    return fuzz.ratio(typed, known) >= FUZZY_RATIO


@dataclass(frozen=True)
class Candidate:
    project_id: int
    name: str
    coverage: float
    score: float
    matched: frozenset[str]


@dataclass(frozen=True)
class Resolution:
    candidates: tuple[Candidate, ...] = ()
    confident: bool = False

    @property
    def best(self) -> Candidate | None:
        return self.candidates[0] if self.candidates else None


@dataclass(frozen=True)
class _Entry:
    project_id: int
    name: str
    weights: dict[str, float]


class ProjectResolver:
    def __init__(self, projects: Iterable[tuple[int, str]]) -> None:
        listed = list(projects)
        self._names = dict(listed)
        tokenized = {pid: set(name_tokens(name)) for pid, name in listed}
        frequency: dict[str, int] = {}
        for tokens in tokenized.values():
            for token in tokens:
                frequency[token] = frequency.get(token, 0) + 1
        total = max(1, len(listed))
        self._frequency = frequency
        self._common = {
            t for t, n in frequency.items() if n > max(MIN_COMMON_FREQUENCY, COMMON_SHARE * total)
        }
        self._common |= {t for t in frequency if t in PLACE_WORDS}
        self._vocabulary = set(frequency)
        self._entries = [
            _Entry(
                pid,
                self._names[pid],
                {t: math.log(1 + total / frequency[t]) for t in tokens},
            )
            for pid, tokens in tokenized.items()
            if tokens
        ]

    @classmethod
    def from_session(cls, session: Session) -> "ProjectResolver":
        rows = session.execute(select(Project.id, Project.name)).all()
        return cls((row.id, row.name) for row in rows)

    def resolve(self, text: str) -> Resolution:
        explicit = self._explicit(text)
        if explicit is not None:
            return Resolution((explicit,), confident=True)
        typed = [t for t in message_tokens(text) if t not in PLACE_WORDS]
        if not typed:
            return Resolution()
        reachable = {
            known for known in self._vocabulary if any(tokens_match(t, known) for t in typed)
        }
        candidates = self._rank(reachable, len(typed))
        return self._decide(candidates) if candidates else Resolution()

    def _explicit(self, text: str) -> Candidate | None:
        match = EXPLICIT_ID.search(normalize(text))
        if not match:
            return None
        project_id = int(match.group(1))
        name = self._names.get(project_id)
        if name is None:
            return None
        return Candidate(project_id, name, 1.0, 1.0, frozenset())

    def _rank(self, reachable: set[str], typed_count: int) -> list[Candidate]:
        ranked: list[Candidate] = []
        for entry in self._entries:
            matched = frozenset(t for t in entry.weights if t in reachable)
            distinct = matched - self._common
            if not distinct:
                continue
            hit = sum(entry.weights[t] for t in matched)
            whole = sum(entry.weights.values())
            if not self._identifies(entry, distinct, typed_count):
                continue
            score = hit - UNMATCHED_PENALTY * (whole - hit)
            ranked.append(Candidate(entry.project_id, entry.name, hit / whole, score, matched))
        return sorted(ranked, key=lambda c: (-c.score, c.name))[:MAX_CANDIDATES]

    def _identifies(self, entry: _Entry, distinct: frozenset[str], typed_count: int) -> bool:
        if any(self._frequency[t] == 1 and len(t) >= ID_TOKEN_LENGTH for t in distinct):
            return True
        own = sum(w for t, w in entry.weights.items() if t not in self._common)
        if sum(entry.weights[t] for t in distinct) / own >= DISTINCT_COVERAGE:
            return True
        return typed_count <= SHORT_QUERY_TOKENS and any(
            self._frequency[t] <= SHORT_QUERY_FREQUENCY and len(t) >= SHORT_QUERY_LENGTH
            for t in distinct
        )

    @staticmethod
    def _decide(candidates: list[Candidate]) -> Resolution:
        top, rest = candidates[0], candidates[1:]
        overlapping = [c for c in rest if c.matched >= top.matched]
        if overlapping and top.coverage < COMPLETE_COVERAGE:
            return Resolution((top, *overlapping))
        close = [
            c
            for c in rest
            if top.score - c.score < MARGIN
            and not (top.coverage >= COMPLETE_COVERAGE and c.coverage < COMPLETE_COVERAGE)
        ]
        if close:
            return Resolution((top, *close))
        return Resolution((top,), confident=True)
