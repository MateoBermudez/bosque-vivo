/** Utilidades del navegador para adjuntar fotos y notas de voz al chat en línea. */

export const MAX_RECORDING_SECONDS = 60;
const MAX_IMAGE_SIDE = 1280;
const AUDIO_RATE = 16_000;

export type EncodedMedia = { base64: string; mimeType: string };

export async function blobToBase64(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let binary = "";
  for (let start = 0; start < bytes.length; start += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(start, start + 0x8000));
  }
  return btoa(binary);
}

/** Reduce la foto a un máximo de 1280 px por lado y la vuelve JPEG, para que viaje liviana. */
export async function encodePhoto(file: Blob): Promise<EncodedMedia> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_IMAGE_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  const context = canvas.getContext("2d");
  if (!context) throw new Error("El navegador no pudo procesar la foto.");
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.8));
  if (!blob) throw new Error("El navegador no pudo procesar la foto.");
  return { base64: await blobToBase64(blob), mimeType: "image/jpeg" };
}

/** Codifica audio mono de 16 bits como WAV, un formato que entienden todos los modelos. */
export function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const write = (offset: number, text: string) => {
    for (let i = 0; i < text.length; i += 1) view.setUint8(offset + i, text.charCodeAt(i));
  };
  write(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  write(8, "WAVE");
  write(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  write(36, "data");
  view.setUint32(40, samples.length * 2, true);
  samples.forEach((sample, index) => {
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + index * 2, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
  });
  return new Blob([buffer], { type: "audio/wav" });
}

async function toWav(recorded: Blob): Promise<EncodedMedia> {
  const context = new AudioContext();
  try {
    const decoded = await context.decodeAudioData(await recorded.arrayBuffer());
    const length = Math.max(1, Math.ceil(decoded.duration * AUDIO_RATE));
    const offline = new OfflineAudioContext(1, length, AUDIO_RATE);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();
    const rendered = await offline.startRendering();
    return { base64: await blobToBase64(encodeWav(rendered.getChannelData(0), AUDIO_RATE)), mimeType: "audio/wav" };
  } finally {
    void context.close();
  }
}

/** Graba una nota de voz con el micrófono; `stop` la devuelve lista para enviar. */
export class VoiceRecorder {
  private recorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;
  startedAt = 0;

  static supported(): boolean {
    return typeof window !== "undefined" && "MediaRecorder" in window && !!navigator.mediaDevices?.getUserMedia;
  }

  async start(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.recorder = new MediaRecorder(this.stream);
    this.recorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.chunks.push(event.data);
    };
    this.recorder.start();
    this.startedAt = Date.now();
  }

  async stop(): Promise<EncodedMedia & { seconds: number }> {
    const recorder = this.recorder;
    if (!recorder) throw new Error("No hay una grabación en curso.");
    const done = new Promise<void>((resolve) => recorder.addEventListener("stop", () => resolve(), { once: true }));
    recorder.stop();
    await done;
    this.release();
    const seconds = Math.round((Date.now() - this.startedAt) / 1000);
    const blob = new Blob(this.chunks, { type: recorder.mimeType || "audio/webm" });
    return { ...(await toWav(blob)), seconds };
  }

  cancel(): void {
    if (this.recorder && this.recorder.state !== "inactive") this.recorder.stop();
    this.release();
  }

  private release(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.recorder = null;
  }
}

export function currentPosition(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("Este navegador no permite compartir la ubicación."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
      () => reject(new Error("No se pudo obtener tu ubicación. Revisa el permiso del navegador.")),
      { enableHighAccuracy: true, timeout: 15_000 },
    );
  });
}
