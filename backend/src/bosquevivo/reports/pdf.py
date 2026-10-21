from fpdf import FPDF

from bosquevivo.db.models import AuditResult, AuditRun, Project

FONT = "Helvetica"


def _latin(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf(
    project: Project,
    run: AuditRun,
    result: AuditResult,
    chart_png: bytes | None,
    chart_path: str | None,
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font(FONT, "B", 18)
    pdf.multi_cell(
        0, 9, _latin(f"Reporte de auditoria: {project.name}"), new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_font(FONT, "", 10)
    pdf.multi_cell(
        0,
        6,
        _latin(
            f"{project.country or 'Pais no registrado'} | {project.source_registry} "
            f"{project.registry_id} | {project.area_ha or 0:.0f} ha"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)
    pdf.set_font(FONT, "B", 28)
    score = "-" if result.score is None else f"{result.score:.0f}"
    pdf.cell(0, 14, f"{score} / 100", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 11)
    pdf.multi_cell(
        0,
        6,
        _latin(
            f"Correspondencia observada: {result.category} | Confianza: "
            f"{result.confidence_label} ({result.confidence:.2f})"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)
    pdf.multi_cell(0, 6, _latin(result.narrative or ""), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font(FONT, "B", 12)
    pdf.cell(0, 8, "Componentes", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 10)
    for name, data in result.components.items():
        if name.startswith("_") or not isinstance(data, dict):
            continue
        puntaje = data.get("puntaje")
        pdf.multi_cell(
            0,
            6,
            _latin(f"- {name}: {'-' if puntaje is None else puntaje}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
    if chart_png and chart_path:
        pdf.ln(2)
        pdf.image(chart_path, w=180)
    pdf.ln(3)
    pdf.set_font(FONT, "B", 12)
    pdf.cell(0, 8, "Trazabilidad", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 9)
    pdf.multi_cell(
        0,
        5,
        _latin(
            f"Corrida {run.id} | indice {run.index_version} | codigo {run.git_sha or 'n/d'} | "
            f"datos {run.dataset_versions}"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)
    pdf.set_font(FONT, "B", 12)
    pdf.cell(0, 8, "Limitaciones", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 9)
    pdf.multi_cell(
        0,
        5,
        _latin(
            "El indice mide la correspondencia entre lo declarado y lo observado; no estima "
            "contrafactuales ni adicionalidad. Las nubes pueden dejar series incompletas. "
            "Este reporte describe lo observado desde el satelite y no atribuye intenciones."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    return bytes(pdf.output())
