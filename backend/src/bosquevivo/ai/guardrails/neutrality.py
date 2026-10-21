import re

ACCUSATORY = (
    "fraude",
    "fraudulent",
    "estafa",
    "estafador",
    "mentira",
    "mentiroso",
    "ladron",
    "ladrón",
    "corrupto",
    "corrupción",
    "criminal",
    "delincuente",
    "culpable",
    "engaño",
    "engañando",
    "robando",
    "mafia",
)

PATTERN = re.compile(r"\b(" + "|".join(re.escape(t) for t in ACCUSATORY) + r")\w*", re.IGNORECASE)


def find_accusatory_terms(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in PATTERN.finditer(text)})
