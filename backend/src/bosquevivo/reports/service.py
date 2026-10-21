import hashlib
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from bosquevivo.audit.compare import compare_declared_observed
from bosquevivo.audit.config import default_config
from bosquevivo.audit.service import AuditService
from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import AuditRun, Project, Report
from bosquevivo.reports.charts import ndvi_chart_png, to_base64
from bosquevivo.reports.pdf import build_pdf

TEMPLATES = Path(__file__).parent / "templates"


class ReportService:
    def __init__(self, session: Session, reports_dir: Path) -> None:
        self.session = session
        self.reports_dir = reports_dir
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"])
        )

    def generate(self, run_id: int, fmt: str = "html") -> Report:
        run = self.session.get(AuditRun, run_id)
        if run is None or run.result is None:
            raise NotFoundError(f"la corrida {run_id} no existe o no tiene resultado")
        project_row = self.session.get(Project, run.project_id)
        if project_row is None:
            raise NotFoundError(f"proyecto {run.project_id} no existe")
        inputs = AuditService(self.session).build_inputs(project_row)
        chart = ndvi_chart_png([(p.period, p.ndvi_mean) for p in inputs.series], inputs.t0)
        folder = self.reports_dir / str(project_row.id)
        folder.mkdir(parents=True, exist_ok=True)
        base = folder / f"run_{run.id}"
        if fmt == "pdf":
            chart_path = None
            if chart:
                chart_path = str(base.with_suffix(".chart.png"))
                Path(chart_path).write_bytes(chart)
            content = build_pdf(project_row, run, run.result, chart, chart_path)
            path = base.with_suffix(".pdf")
            path.write_bytes(content)
        else:
            sensitivity = run.result.components.get("_sensibilidad") or {}
            components = [
                (name, data)
                for name, data in run.result.components.items()
                if not name.startswith("_") and isinstance(data, dict)
            ]
            html = self.env.get_template("report.html.j2").render(
                project=project_row,
                run=run,
                result=run.result,
                components=components,
                sensitivity=sensitivity,
                sensitivity_delta=default_config().sensitivity_delta,
                sensor=run.result.components.get("_sensor", "n/d"),
                chart=to_base64(chart),
                comparison=compare_declared_observed(inputs),
            )
            content = html.encode("utf-8")
            path = base.with_suffix(".html")
            path.write_bytes(content)
        report = Report(
            run_id=run.id, format=fmt, path=str(path), sha256=hashlib.sha256(content).hexdigest()
        )
        self.session.add(report)
        self.session.flush()
        return report
