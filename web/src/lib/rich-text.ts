// Mini-parser de Markdown para las respuestas del asistente: párrafos, listas con viñetas,
// **negrita**, *cursiva* y `código`. Produce una estructura de datos (no HTML), así el
// componente que la dibuja nunca inserta HTML crudo.

export type Inline = { kind: "text" | "bold" | "italic" | "code"; value: string };
export type Block =
  | { kind: "paragraph"; content: Inline[] }
  | { kind: "list"; items: Inline[][] };

// Los marcadores deben ir pegados al texto: así «2 * 3 = 6» no se confunde con cursiva.
const INLINE = /(\*\*(?!\s)[^*\n]+?(?<!\s)\*\*|\*(?!\s)[^*\n]+?(?<!\s)\*|`[^`\n]+`)/g;

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  for (const part of text.split(INLINE)) {
    if (!part) continue;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      out.push({ kind: "bold", value: part.slice(2, -2) });
    } else if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      out.push({ kind: "code", value: part.slice(1, -1) });
    } else if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      out.push({ kind: "italic", value: part.slice(1, -1) });
    } else {
      out.push({ kind: "text", value: part });
    }
  }
  return out;
}

const BULLET = /^\s*[-*•]\s+(.*)$/;

export function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let list: Inline[][] = [];

  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ kind: "paragraph", content: parseInline(paragraph.join(" ")) });
    paragraph = [];
  };
  const flushList = () => {
    if (list.length) blocks.push({ kind: "list", items: list });
    list = [];
  };

  for (const line of text.replaceAll("\r\n", "\n").split("\n")) {
    const bullet = BULLET.exec(line);
    if (bullet) {
      flushParagraph();
      list.push(parseInline(bullet[1] ?? ""));
    } else if (line.trim() === "") {
      flushParagraph();
      flushList();
    } else {
      flushList();
      paragraph.push(line.trim());
    }
  }
  flushParagraph();
  flushList();
  return blocks;
}
