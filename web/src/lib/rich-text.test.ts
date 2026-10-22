import { describe, expect, it } from "vitest";

import { parseBlocks, parseInline } from "./rich-text";

describe("parseInline", () => {
  it("separa negrita, cursiva y código", () => {
    expect(parseInline("hola **mundo** y *tú* con `x`")).toEqual([
      { kind: "text", value: "hola " },
      { kind: "bold", value: "mundo" },
      { kind: "text", value: " y " },
      { kind: "italic", value: "tú" },
      { kind: "text", value: " con " },
      { kind: "code", value: "x" },
    ]);
  });

  it("deja como texto los marcadores sin cerrar", () => {
    expect(parseInline("2 * 3 = 6 y **sin cerrar")).toEqual([{ kind: "text", value: "2 * 3 = 6 y **sin cerrar" }]);
  });

  it("no interpreta HTML: lo deja como texto literal", () => {
    expect(parseInline("<script>alert(1)</script>")).toEqual([
      { kind: "text", value: "<script>alert(1)</script>" },
    ]);
  });
});

describe("parseBlocks", () => {
  it("agrupa líneas en párrafos y viñetas", () => {
    const blocks = parseBlocks("Primera línea\nsigue aquí\n\n- uno\n- **dos**\n\nFin");
    expect(blocks).toEqual([
      { kind: "paragraph", content: [{ kind: "text", value: "Primera línea sigue aquí" }] },
      {
        kind: "list",
        items: [[{ kind: "text", value: "uno" }], [{ kind: "bold", value: "dos" }]],
      },
      { kind: "paragraph", content: [{ kind: "text", value: "Fin" }] },
    ]);
  });

  it("devuelve una lista vacía para texto vacío", () => {
    expect(parseBlocks("  \n\n ")).toEqual([]);
  });

  it("acepta saltos de línea de Windows", () => {
    expect(parseBlocks("a\r\n\r\nb")).toHaveLength(2);
  });
});
