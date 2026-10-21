import base64
import io
from datetime import date

import matplotlib
import matplotlib.dates as mdates

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def ndvi_chart_png(points: list[tuple[date, float | None]], t0: date | None) -> bytes | None:
    valid = [(d, v) for d, v in points if v is not None]
    if len(valid) < 2:
        return None
    figure, axis = plt.subplots(figsize=(8, 3), dpi=110)
    axis.plot(
        [mdates.date2num(d) for d, _ in valid],
        [v for _, v in valid],
        color="#2f7d46",
        linewidth=1.5,
    )
    axis.xaxis_date()
    if t0 is not None:
        axis.axvline(
            float(mdates.date2num(t0)),
            color="#b5651d",
            linestyle="--",
            linewidth=1,
            label="Acreditación (T0)",
        )
        axis.legend(loc="lower left")
    axis.set_ylabel("NDVI")
    axis.set_ylim(0, 1)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png")
    plt.close(figure)
    return buffer.getvalue()


def to_base64(content: bytes | None) -> str | None:
    return base64.b64encode(content).decode() if content else None
