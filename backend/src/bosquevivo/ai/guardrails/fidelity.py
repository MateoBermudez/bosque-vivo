import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

NUMBER = re.compile(r"(?<![\w.,])\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?")


def parse_number(token: str) -> float | None:
    cleaned = token.strip()
    if re.fullmatch(r"\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?", cleaned):
        cleaned = cleaned.replace(".", "").replace(" ", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def collect_numbers(value: Any) -> set[float]:
    found: set[float] = set()

    def walk(item: Any) -> None:
        if isinstance(item, bool) or item is None:
            return
        if isinstance(item, int | float):
            found.add(float(item))
        elif isinstance(item, datetime | date):
            found.update({float(item.year), float(item.month), float(item.day)})
        elif isinstance(item, str):
            for token in NUMBER.findall(item):
                number = parse_number(token)
                if number is not None:
                    found.add(number)
        elif isinstance(item, dict):
            for key, sub in item.items():
                walk(key)
                walk(sub)
        elif isinstance(item, list | tuple | set):
            for sub in item:
                walk(sub)

    walk(value)
    return found


def decimals_of(token: str) -> int:
    if re.fullmatch(r"\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?", token.strip()):
        return len(token.split(",")[1]) if "," in token else 0
    match = re.search(r"[.,](\d+)$", token)
    return len(match.group(1)) if match else 0


def matches(number: float, decimals: int, evidence: set[float]) -> bool:
    for known in evidence:
        if round(known, decimals) == round(number, decimals):
            return True
        if decimals == 0 and abs(known - number) < 0.5 and abs(known) >= 1:
            return round(known) == round(number)
    return False


@dataclass
class FidelityReport:
    passed: bool
    unsupported: list[str] = field(default_factory=list)


def check_fidelity(
    answer: str, evidence_payloads: list[Any], allowed_context: list[str] | None = None
) -> FidelityReport:
    evidence = collect_numbers(evidence_payloads)
    for text in allowed_context or []:
        evidence |= collect_numbers(text)
    unsupported: list[str] = []
    for token in NUMBER.findall(answer):
        number = parse_number(token)
        if number is None:
            continue
        if not matches(number, decimals_of(token), evidence):
            unsupported.append(token)
    return FidelityReport(passed=not unsupported, unsupported=unsupported)
