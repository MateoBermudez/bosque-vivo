import pytest

from bosquevivo.ai.knowledge import KnowledgeBase, tokenize


@pytest.fixture
def kb(db):
    base = KnowledgeBase(db)
    assert base.load_directory() > 10
    return base


def test_tokenize_removes_accents_and_stopwords():
    assert tokenize("¿Qué es el índice de confianza?") == ["indice", "confianza"]


def test_search_finds_ndvi_definition(kb):
    hits = kb.search("¿Qué es el NDVI?")
    assert hits and hits[0].title == "NDVI"


def test_search_finds_data_protection_law(kb):
    hits = kb.search("datos personales supresión autorización")
    assert hits[0].source.startswith("normativa")
    assert "1581" in hits[0].content or "1581" in hits[0].title


def test_search_returns_citation(kb):
    hit = kb.search("nubes datos insuficientes")[0]
    assert " · " in hit.citation


def test_unrelated_query_returns_nothing(kb):
    assert kb.search("receta de arepas con queso") == []


def test_reload_replaces_chunks(db):
    base = KnowledgeBase(db)
    first = base.load_directory()
    second = base.load_directory()
    assert first == second
