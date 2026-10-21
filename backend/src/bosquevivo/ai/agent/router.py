import re
from typing import Literal

DEEP = re.compile(
    r"(analiz|imagen|imágenes|foto|sat[eé]lite|antes y despu[eé]s|tala\w*\s+cerca|compar)",
    re.IGNORECASE,
)

QueryClass = Literal["rapida", "profunda"]


def classify_query(text: str, has_media: bool = False) -> QueryClass:
    return "profunda" if has_media or DEEP.search(text) else "rapida"
