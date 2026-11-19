import { describe, expect, it } from "vitest";

import { blobToBase64, encodeWav } from "./media";

describe("notas de voz", () => {
  it("codifica WAV mono de 16 bits con cabecera válida", async () => {
    const wav = encodeWav(new Float32Array([0, 1, -1, 0.5]), 16_000);
    expect(wav.type).toBe("audio/wav");
    const view = new DataView(await wav.arrayBuffer());
    const text = (offset: number) => String.fromCharCode(...new Uint8Array(view.buffer, offset, 4));
    expect(text(0)).toBe("RIFF");
    expect(text(8)).toBe("WAVE");
    expect(view.getUint16(22, true)).toBe(1);
    expect(view.getUint32(24, true)).toBe(16_000);
    expect(view.getUint32(40, true)).toBe(8);
    expect(view.getInt16(46, true)).toBe(0x7fff);
    expect(view.getInt16(48, true)).toBe(-0x8000);
  });

  it("convierte archivos a base64", async () => {
    expect(await blobToBase64(new Blob(["hola"]))).toBe("aG9sYQ==");
  });
});
