import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import docx
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "plantilla" / "Formato_ieee829.docx"
PROJECT = "Bosque Vivo"
TEXT_WIDTH = 8809
TOC_DEPTH = 2

PLAN_LEVELS = {
    ("Criterios de Aceptación", 3): 1,
    ("Entregables", 3): 1,
    ("Riesgos", 2): 2,
}
ANNEXES = [
    ("casos-de-prueba.md", "Anexo A. Especificación de casos de prueba"),
    ("informe-de-resultados.md", "Anexo B. Informe de resultados"),
    ("incidencias.md", "Anexo C. Registro de incidencias"),
]


def ast(path: Path) -> list:
    out = subprocess.run(
        ["pandoc", str(path), "-f", "markdown-yaml_metadata_block", "-t", "json"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["blocks"]


def strip_number(text: str) -> str:
    return re.sub(r"^\d+(\.\d+)*\.?\s+", "", text).strip()


class Builder:
    def __init__(self, document: docx.Document, date: str) -> None:
        self.doc = document
        self.body = document.element.body
        self.date = date
        paragraphs = document.paragraphs
        by_text = {p.text.strip(): p for p in paragraphs if p.text.strip()}
        self.h1 = by_text["Historial de Versiones"]._p
        self.h2 = by_text["Elementos de Pruebas"]._p
        self.text = next(p for p in paragraphs if p.text.startswith("Listado de todos"))._p
        self.bullet = by_text["Dependencias con Desarrollos."]._p
        self.sdt = self.body.find(qn("w:sdt"))
        self.toc_entries = self.sdt.findall(".//" + qn("w:p"))
        self.toc_level1 = self.toc_entries[1]
        self.toc_level2 = self.toc_entries[4]
        self.headings: list[tuple[int, str, str]] = []
        self.anchor = 9000
        self.cursor = None

    def fill_cover(self) -> None:
        for p in self.doc.paragraphs[:20]:
            for run in p.runs:
                if "[Nombre del Proyecto]" in run.text:
                    run.text = run.text.replace("[Nombre del Proyecto]", PROJECT).strip()
                    run.font.color.rgb = docx.shared.RGBColor(0, 0, 0)
                if "[dd/mm/aaaa]" in run.text:
                    run.text = run.text.replace("[dd/mm/aaaa]", self.date)
                    run.font.color.rgb = docx.shared.RGBColor(0, 0, 0)
            if "Fecha:" in p.text and "[" in p.text:
                for run in p.runs:
                    if run.text in ("[", "]") or run.text.strip() in ("[", "]"):
                        run.text = ""
                    elif "dd/mm/aaaa" in run.text:
                        run.text = self.date
                        run.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

    def clear_body(self) -> None:
        kids = list(self.body)
        start = kids.index(self.sdt) + 1
        for node in kids[start:]:
            if node.tag != qn("w:sectPr"):
                self.body.remove(node)
        self.cursor = self.sdt

    def append(self, node) -> None:
        self.cursor.addnext(node)
        self.cursor = node

    def page_break(self) -> None:
        p = OxmlElement("w:p")
        r = OxmlElement("w:r")
        br = OxmlElement("w:br")
        br.set(qn("w:type"), "page")
        r.append(br)
        p.append(r)
        self.append(p)

    @staticmethod
    def _run_props(paragraph):
        for r in paragraph.iter(qn("w:r")):
            t = r.find(qn("w:t"))
            if t is not None and (t.text or "").strip() and r.find(qn("w:rPr")) is not None:
                return copy.deepcopy(r.find(qn("w:rPr")))
        return OxmlElement("w:rPr")

    def _paragraph_from(self, prototype, color: str | None = "000000"):
        p = OxmlElement("w:p")
        ppr = copy.deepcopy(prototype.find(qn("w:pPr")))
        if color:
            for c in ppr.iter(qn("w:color")):
                c.set(qn("w:val"), color)
        p.append(ppr)
        rpr = self._run_props(prototype)
        if color:
            for c in rpr.iter(qn("w:color")):
                c.set(qn("w:val"), color)
        rtl = rpr.find(qn("w:rtl"))
        if rtl is not None:
            rpr.remove(rtl)
        return p, rpr

    def heading(self, level: int, text: str, numbered: bool = True) -> None:
        prototype = self.h1 if level == 1 else self.h2
        p, rpr = self._paragraph_from(prototype, color=None)
        ppr = p.find(qn("w:pPr"))
        style = OxmlElement("w:pStyle")
        style.set(qn("w:val"), f"Heading{level}")
        ppr.insert(0, style)
        for c in list(ppr.iter(qn("w:color"))):
            c.set(qn("w:val"), "365F91")
        if level == 3:
            for size in list(rpr.iter(qn("w:sz"))) + list(rpr.iter(qn("w:szCs"))):
                size.set(qn("w:val"), "22")
        keep = OxmlElement("w:keepNext")
        ppr.insert(1, keep)
        self.anchor += 1
        name = f"_bv{self.anchor:04d}"
        start = OxmlElement("w:bookmarkStart")
        start.set(qn("w:id"), str(self.anchor))
        start.set(qn("w:name"), name)
        p.append(start)
        r = OxmlElement("w:r")
        r.append(rpr)
        t = OxmlElement("w:t")
        t.text = text
        t.set(qn("xml:space"), "preserve")
        r.append(t)
        p.append(r)
        end = OxmlElement("w:bookmarkEnd")
        end.set(qn("w:id"), str(self.anchor))
        p.append(end)
        self.append(p)
        if level <= TOC_DEPTH:
            self.headings.append((level, text, name))

    def _runs(self, inlines, rpr, out: list, bold=False, italic=False, code=False, link=None):
        for item in inlines:
            kind = item["t"]
            content = item.get("c")
            if kind == "Str":
                out.append((content, bold, italic, code, link))
            elif kind in ("Space", "SoftBreak"):
                out.append((" ", bold, italic, code, link))
            elif kind == "LineBreak":
                out.append(("\n", bold, italic, code, link))
            elif kind == "Strong":
                self._runs(content, rpr, out, True, italic, code, link)
            elif kind == "Emph":
                self._runs(content, rpr, out, bold, True, code, link)
            elif kind == "Code":
                out.append((content[1], bold, italic, True, link))
            elif kind == "Link":
                target = content[2][0]
                url = target if target.startswith("http") else None
                self._runs(content[1], rpr, out, bold, italic, code, url)
            elif kind == "Quoted":
                mark = "“" if content[0]["t"] == "DoubleQuote" else "‘"
                close = "”" if mark == "“" else "’"
                out.append((mark, bold, italic, code, link))
                self._runs(content[1], rpr, out, bold, italic, code, link)
                out.append((close, bold, italic, code, link))
            elif kind in ("Strikeout", "Superscript", "Subscript", "SmallCaps", "Underline"):
                self._runs(content, rpr, out, bold, italic, code, link)
            elif kind == "Span":
                self._runs(content[1], rpr, out, bold, italic, code, link)
            elif kind == "Math":
                out.append((content[1], bold, italic, code, link))
            elif kind == "RawInline":
                continue
        return out

    def _emit_runs(self, p, inlines, rpr, size: int | None = None) -> None:
        pieces = self._runs(inlines, rpr, [])
        merged: list[list] = []
        for piece in pieces:
            if merged and merged[-1][1:] == list(piece[1:]):
                merged[-1][0] += piece[0]
            else:
                merged.append(list(piece))
        for text, bold, italic, code, link in merged:
            r = OxmlElement("w:r")
            props = copy.deepcopy(rpr)
            for tag in ("w:b", "w:bCs", "w:i", "w:iCs"):
                for node in props.findall(qn(tag)):
                    props.remove(node)
            if bold:
                props.insert(1, OxmlElement("w:b"))
            if italic:
                props.insert(1, OxmlElement("w:i"))
            if code:
                fonts = props.find(qn("w:rFonts"))
                for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                    fonts.set(qn(attr), "Courier New")
            if size:
                for node in list(props.iter(qn("w:sz"))) + list(props.iter(qn("w:szCs"))):
                    node.set(qn("w:val"), str(size))
            if link:
                color = props.find(qn("w:color"))
                if color is not None:
                    color.set(qn("w:val"), "1155CC")
                u = OxmlElement("w:u")
                u.set(qn("w:val"), "single")
                props.append(u)
            r.append(props)
            for i, chunk in enumerate(text.split("\n")):
                if i:
                    r.append(OxmlElement("w:br"))
                t = OxmlElement("w:t")
                t.text = chunk
                t.set(qn("xml:space"), "preserve")
                r.append(t)
            if link:
                rid = self.doc.part.relate_to(link, RT.HYPERLINK, is_external=True)
                h = OxmlElement("w:hyperlink")
                h.set(qn("r:id"), rid)
                h.append(r)
                p.append(h)
            else:
                p.append(r)

    def paragraph(self, inlines, *, size=None, after=120, align=None, indent=None) -> None:
        p, rpr = self._paragraph_from(self.text)
        ppr = p.find(qn("w:pPr"))
        for node in ppr.findall(qn("w:rPr")):
            ppr.remove(node)
        spacing = OxmlElement("w:spacing")
        spacing.set(qn("w:after"), str(after))
        spacing.set(qn("w:line"), "276")
        spacing.set(qn("w:lineRule"), "auto")
        jc = ppr.find(qn("w:jc"))
        if align and jc is not None:
            jc.set(qn("w:val"), align)
        (jc if jc is not None else ppr[-1]).addprevious(spacing)
        if indent:
            ind = OxmlElement("w:ind")
            ind.set(qn("w:left"), str(indent))
            spacing.addnext(ind)
        self._emit_runs(p, inlines, rpr, size)
        self.append(p)

    def list_item(self, blocks, ordered_label: str | None, depth: int) -> None:
        first = True
        for block in blocks:
            if block["t"] in ("Plain", "Para") and first:
                if ordered_label is None:
                    p, rpr = self._paragraph_from(self.bullet)
                    ppr = p.find(qn("w:pPr"))
                    ppr.find(qn("w:numPr")).find(qn("w:ilvl")).set(qn("w:val"), str(depth))
                    ind = ppr.find(qn("w:ind"))
                    ind.set(qn("w:left"), str(720 + 360 * depth))
                    spacing = OxmlElement("w:spacing")
                    spacing.set(qn("w:after"), "60")
                    ind.addprevious(spacing)
                    rpr = self._run_props(self.text)
                    for c in rpr.iter(qn("w:color")):
                        c.set(qn("w:val"), "000000")
                    self._emit_runs(p, block["c"], rpr)
                    self.append(p)
                else:
                    inlines = [{"t": "Str", "c": ordered_label + " "}] + block["c"]
                    self.paragraph(inlines, after=60, indent=360 + 360 * depth, align="left")
                first = False
            else:
                self.block(block, depth + 1)

    def table(self, content) -> None:
        _, _, colspecs, head, bodies, _ = content
        rows = []
        for row in head[1]:
            rows.append((True, [cell[4] for cell in row[1]]))
        for body in bodies:
            for row in body[2] + body[3]:
                rows.append((False, [cell[4] for cell in row[1]]))
        ncols = len(colspecs)
        if ncols >= 7 and rows and rows[0][0]:
            labels = rows[0][1]
            for _, cells in rows[1:]:
                self.table_rows(
                    [(False, [label, cell]) for label, cell in zip(labels, cells, strict=False)],
                    [1900, TEXT_WIDTH - 1900],
                    label_column=True,
                )
            return
        self.table_rows(rows, column_widths(rows, ncols))

    def table_rows(self, rows, widths, label_column: bool = False) -> None:
        ncols = len(widths)
        tbl = OxmlElement("w:tbl")
        tblpr = OxmlElement("w:tblPr")
        tblw = OxmlElement("w:tblW")
        tblw.set(qn("w:w"), str(TEXT_WIDTH))
        tblw.set(qn("w:type"), "dxa")
        tblpr.append(tblw)
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tblpr.append(layout)
        tbl.append(tblpr)
        grid = OxmlElement("w:tblGrid")
        for w in widths:
            col = OxmlElement("w:gridCol")
            col.set(qn("w:w"), str(w))
            grid.append(col)
        tbl.append(grid)
        for header, cells in rows:
            tr = OxmlElement("w:tr")
            trpr = OxmlElement("w:trPr")
            cant = OxmlElement("w:cantSplit")
            trpr.append(cant)
            if header:
                trpr.append(OxmlElement("w:tblHeader"))
            tr.append(trpr)
            for i in range(ncols):
                blocks = cells[i] if i < len(cells) else []
                tc = OxmlElement("w:tc")
                tcpr = OxmlElement("w:tcPr")
                tcw = OxmlElement("w:tcW")
                tcw.set(qn("w:w"), str(widths[i]))
                tcw.set(qn("w:type"), "dxa")
                tcpr.append(tcw)
                borders = OxmlElement("w:tcBorders")
                for side in ("top", "left", "bottom", "right"):
                    b = OxmlElement(f"w:{side}")
                    b.set(qn("w:val"), "single")
                    b.set(qn("w:sz"), "4")
                    b.set(qn("w:space"), "0")
                    b.set(qn("w:color"), "000000")
                    borders.append(b)
                tcpr.append(borders)
                if header or (label_column and i == 0):
                    shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear")
                    shd.set(qn("w:fill"), "D9D9D9")
                    tcpr.append(shd)
                tc.append(tcpr)
                self._cell(tc, blocks, header, bold=label_column and i == 0)
                tr.append(tc)
            tbl.append(tr)
        self.append(tbl)
        spacer = OxmlElement("w:p")
        self.append(spacer)

    def _cell(self, tc, blocks, header: bool, bold: bool = False) -> None:
        inlines_list = []
        for block in blocks:
            if block["t"] in ("Plain", "Para"):
                inlines_list.append(block["c"])
            elif block["t"] in ("BulletList", "OrderedList"):
                for item in block["c"] if block["t"] == "BulletList" else block["c"][1]:
                    for b in item:
                        if b["t"] in ("Plain", "Para"):
                            inlines_list.append([{"t": "Str", "c": "• "}] + b["c"])
        if not inlines_list:
            inlines_list = [[]]
        for inlines in inlines_list:
            p = OxmlElement("w:p")
            ppr = OxmlElement("w:pPr")
            spacing = OxmlElement("w:spacing")
            spacing.set(qn("w:before"), "20")
            spacing.set(qn("w:after"), "20")
            ppr.append(spacing)
            if header:
                jc = OxmlElement("w:jc")
                jc.set(qn("w:val"), "center")
                ppr.append(jc)
            p.append(ppr)
            rpr = OxmlElement("w:rPr")
            fonts = OxmlElement("w:rFonts")
            for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                fonts.set(qn(attr), "Arial")
            rpr.append(fonts)
            color = OxmlElement("w:color")
            color.set(qn("w:val"), "000000")
            rpr.append(color)
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), "18")
            rpr.append(sz)
            szcs = OxmlElement("w:szCs")
            szcs.set(qn("w:val"), "18")
            rpr.append(szcs)
            if header or bold:
                inlines = [{"t": "Strong", "c": inlines}]
            self._emit_runs(p, inlines, rpr)
            tc.append(p)

    def code(self, text: str) -> None:
        for line in text.split("\n"):
            p, rpr = self._paragraph_from(self.text)
            ppr = p.find(qn("w:pPr"))
            for node in ppr.findall(qn("w:rPr")):
                ppr.remove(node)
            shd = ppr.find(qn("w:shd"))
            if shd is not None:
                shd.set(qn("w:fill"), "F2F2F2")
            spacing = OxmlElement("w:spacing")
            spacing.set(qn("w:after"), "0")
            ind = OxmlElement("w:ind")
            ind.set(qn("w:left"), "284")
            jc = ppr.find(qn("w:jc"))
            if jc is not None:
                jc.set(qn("w:val"), "left")
                jc.addprevious(spacing)
                jc.addprevious(ind)
            self._emit_runs(p, [{"t": "Code", "c": [None, line]}], rpr, size=18)
            self.append(p)
        self.append(OxmlElement("w:p"))

    def block(self, block, depth: int = 0) -> None:
        kind = block["t"]
        content = block.get("c")
        if kind in ("Para", "Plain"):
            self.paragraph(content)
        elif kind == "BulletList":
            for item in content:
                self.list_item(item, None, depth)
        elif kind == "OrderedList":
            start = content[0][0]
            for n, item in enumerate(content[1], start):
                self.list_item(item, f"{n}.", depth)
        elif kind == "Table":
            self.table(content)
        elif kind == "CodeBlock":
            self.code(content[1])
        elif kind == "BlockQuote":
            for inner in content:
                self.block(inner, depth + 1)
        elif kind == "Header":
            raise ValueError("los títulos se procesan aparte")

    def toc(self) -> None:
        for node in list(self.sdt.find(qn("w:sdtContent"))):
            self.sdt.find(qn("w:sdtContent")).remove(node)
        content = self.sdt.find(qn("w:sdtContent"))
        last = len(self.headings) - 1
        for index, (level, text, anchor) in enumerate(self.headings):
            prototype = self.toc_level1 if level == 1 else self.toc_level2
            p = OxmlElement("w:p")
            p.append(copy.deepcopy(prototype.find(qn("w:pPr"))))
            rpr = self._run_props(prototype)
            rtl = rpr.find(qn("w:rtl"))
            if rtl is not None:
                rpr.remove(rtl)
            if index == 0:
                r = OxmlElement("w:r")
                begin = OxmlElement("w:fldChar")
                begin.set(qn("w:fldCharType"), "begin")
                r.append(begin)
                instr = OxmlElement("w:instrText")
                instr.set(qn("xml:space"), "preserve")
                instr.text = ' TOC \\h \\u \\z \\t "Heading 1,1,Heading 2,2," '
                r.append(instr)
                sep = OxmlElement("w:fldChar")
                sep.set(qn("w:fldCharType"), "separate")
                r.append(sep)
                p.append(r)
            link = OxmlElement("w:hyperlink")
            link.set(qn("w:anchor"), anchor)
            for piece in (text, "\t", "0"):
                r = OxmlElement("w:r")
                r.append(copy.deepcopy(rpr))
                if piece == "\t":
                    r.append(OxmlElement("w:tab"))
                else:
                    t = OxmlElement("w:t")
                    t.text = piece
                    t.set(qn("xml:space"), "preserve")
                    r.append(t)
                link.append(r)
            p.append(link)
            if index == last:
                r = OxmlElement("w:r")
                end = OxmlElement("w:fldChar")
                end.set(qn("w:fldCharType"), "end")
                r.append(end)
                p.append(r)
            content.append(p)

    def set_toc_pages(self, pages: list[int]) -> None:
        entries = self.sdt.find(qn("w:sdtContent")).findall(qn("w:p"))
        for entry, page in zip(entries, pages, strict=True):
            texts = list(entry.iter(qn("w:t")))
            texts[-1].text = str(page)


def column_widths(rows, ncols: int) -> list[int]:
    char = 108
    need = [4] * ncols
    total_len = [0] * ncols
    filled = [0] * ncols
    for header, cells in rows:
        for i, blocks in enumerate(cells[:ncols]):
            text = plain_text(blocks)
            longest = max((len(w) for w in re.split(r"\s+", text)), default=0)
            need[i] = max(need[i], min(14, longest) + (3 if header else 1))
            if not header and text.strip():
                total_len[i] += len(text)
                filled[i] += 1
    desire = []
    for i in range(ncols):
        average = total_len[i] / filled[i] if filled[i] else 12
        desire.append(max(need[i], min(average, 45)))
    minimum = [n * char for n in need]
    fixed: dict[int, float] = {}
    while True:
        free = [i for i in range(ncols) if i not in fixed]
        room = TEXT_WIDTH - sum(fixed.values())
        weight = sum(desire[i] for i in free) or 1
        widths = {i: room * desire[i] / weight for i in free}
        short = [i for i in free if widths[i] < minimum[i]]
        if not short or len(fixed) + len(short) == ncols:
            break
        for i in short:
            fixed[i] = minimum[i]
    widths.update(fixed)
    return [int(widths[i]) for i in range(ncols)]


def plain_text(blocks) -> str:
    out = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("t") == "Str":
                out.append(node["c"])
            elif node.get("t") in ("Space", "SoftBreak"):
                out.append(" ")
            elif node.get("t") == "Code":
                out.append(node["c"][1])
            else:
                walk(node.get("c"))
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(blocks)
    return "".join(out)


def build(date: str) -> Builder:
    document = docx.Document(str(TEMPLATE))
    builder = Builder(document, date)
    builder.fill_cover()
    builder.clear_body()
    builder.page_break()
    seen: dict[str, int] = {}
    first_h1 = True
    for block in ast(ROOT / "plan-de-pruebas.md"):
        if block["t"] == "Header":
            md_level = block["c"][0]
            title = strip_number(plain_text(block["c"][2]))
            if md_level == 1:
                continue
            seen[title] = seen.get(title, 0) + 1
            level = PLAN_LEVELS.get((title, md_level), {2: 1, 3: 2, 4: 2}.get(md_level, 2))
            if title == "Criterios de Aceptación" and md_level == 4:
                level = 2
            if (
                level == 1
                and not first_h1
                and title
                not in (
                    "Información del Proyecto",
                    "Aprobaciones",
                    "Alcance y Estrategia de las Pruebas",
                    "Glosario",
                )
            ):
                builder.page_break()
            first_h1 = False if level == 1 else first_h1
            builder.started = True
            builder.heading(level, title)
            continue
        if not getattr(builder, "started", False):
            continue
        builder.block(block)
    for source, title in ANNEXES:
        builder.page_break()
        builder.heading(1, title)
        for block in ast(ROOT / source):
            if block["t"] == "Header":
                md_level = block["c"][0]
                if md_level == 1:
                    continue
                text = plain_text(block["c"][2])
                builder.heading(2 if md_level == 2 else 3, text)
            else:
                builder.block(block)
    builder.toc()
    return builder


def pdf_pages(pdf: Path) -> list[str]:
    count = int(
        re.search(
            r"Pages:\s+(\d+)",
            subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout,
        ).group(1)
    )
    return [
        subprocess.run(
            ["pdftotext", "-layout", "-f", str(i), "-l", str(i), str(pdf), "-"],
            capture_output=True,
            text=True,
        ).stdout
        for i in range(1, count + 1)
    ]


def render(docx_path: Path, out_dir: Path) -> Path:
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)],
        check=True,
        capture_output=True,
    )
    return out_dir / (docx_path.stem + ".pdf")


def find_pages(builder: Builder, pages: list[str]) -> list[int]:
    found = []
    start = 2
    for _, text, _ in builder.headings:
        key = re.sub(r"\s+", " ", text)[:45]
        page = None
        for i in range(start, len(pages)):
            lines = [re.sub(r"\s+", " ", line).strip() for line in pages[i].splitlines()]
            if any(line.startswith(key) and not re.search(r"\s\d+$", line) for line in lines):
                page = i + 1
                break
        if page is None:
            raise SystemExit(f"no se encontró la página de «{text}»")
        found.append(page)
        start = page - 1
    return found


def main() -> None:
    out_docx = ROOT / "Plan_de_Pruebas_Bosque_Vivo.docx"
    work = Path(sys.argv[1])
    date = sys.argv[2]
    builder = build(date)
    builder.doc.core_properties.title = "Plan de Pruebas de Software — Bosque Vivo"
    builder.doc.core_properties.author = "Equipo Bosque Vivo"
    builder.doc.core_properties.last_modified_by = "Mateo Bermúdez Cuartas"
    draft = work / "Plan_de_Pruebas_Bosque_Vivo.docx"
    builder.doc.save(str(draft))
    pages = find_pages(builder, pdf_pages(render(draft, work)))
    builder.set_toc_pages(pages)
    builder.doc.save(str(out_docx))
    final = render(out_docx, work)
    check = find_pages(builder, pdf_pages(final))
    if check != pages:
        builder.set_toc_pages(check)
        builder.doc.save(str(out_docx))
        final = render(out_docx, work)
    final.replace(ROOT / "Plan_de_Pruebas_Bosque_Vivo.pdf")


if __name__ == "__main__":
    main()
