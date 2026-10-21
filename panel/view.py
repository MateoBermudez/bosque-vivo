import pandas as pd


def ndvi_frame(series: dict) -> pd.DataFrame:
    frame = pd.DataFrame(series.get("ndvi", []))
    if frame.empty:
        return frame
    frame["period"] = pd.to_datetime(frame["period"])
    return frame.sort_values("period")


def components_frame(components: dict) -> pd.DataFrame:
    rows = [
        {"componente": name, "puntaje": data.get("puntaje")}
        for name, data in components.items()
        if not name.startswith("_") and isinstance(data, dict)
    ]
    return pd.DataFrame(rows)


def category_color(category: str) -> str:
    return {
        "Alta": "#2f7d46",
        "Media": "#c58a1b",
        "Baja": "#b5422c",
        "Insuficiente": "#6b7280",
    }.get(category, "#6b7280")


def centroid(feature: dict) -> tuple[float, float]:
    coords = feature["geometry"]["coordinates"]
    flat: list[list[float]] = []

    def walk(item: list) -> None:
        if item and isinstance(item[0], int | float):
            flat.append(item)
        else:
            for sub in item:
                walk(sub)

    walk(coords)
    lons = [c[0] for c in flat]
    lats = [c[1] for c in flat]
    return sum(lats) / len(lats), sum(lons) / len(lons)
