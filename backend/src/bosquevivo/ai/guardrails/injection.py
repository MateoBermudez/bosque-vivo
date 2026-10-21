import re
from dataclasses import dataclass, field

PATTERNS = (
    r"ignor[ae]\s+(todas\s+)?(las\s+)?(instrucciones|reglas)",
    r"olvida\s+(todo|tus\s+instrucciones|las\s+reglas)",
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)",
    r"disregard\s+(the\s+)?(system|previous)",
    r"(muestra|revela|dime|imprime|show|reveal|print)\s+.{0,30}(prompt|instrucciones\s+del\s+sistema|system\s+prompt)",
    r"(clave|token|api[\s_-]?key|secreto|password|contraseña)",
    r"act[uú]a\s+como\s+(si\s+fueras\s+)?(un\s+)?(administrador|admin|root)",
    r"you\s+are\s+now\s+",
    r"nuevas?\s+instrucciones\s*:",
)
COMPILED = [re.compile(p, re.IGNORECASE) for p in PATTERNS]


@dataclass
class InjectionReport:
    suspicious: bool
    matches: list[str] = field(default_factory=list)


def scan_for_injection(text: str) -> InjectionReport:
    hits = [m.group(0) for pattern in COMPILED if (m := pattern.search(text))]
    return InjectionReport(suspicious=bool(hits), matches=hits)


def wrap_untrusted(text: str, label: str) -> str:
    cleaned = text.replace("<", "\u2039").replace(">", "\u203a")
    return f"<{label}>\n{cleaned}\n</{label}>"
