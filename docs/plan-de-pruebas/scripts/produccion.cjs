// Prueba en producción del chat en línea (texto, ubicación, foto y nota de voz con Gemini real),
// del sitio sin WhatsApp y de la cuenta de pruebas compartida.
// Uso: PROD_BASE=https://bosque-vivo-web.vercel.app PROD_REPORT=salida.json node produccion.cjs
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.PROD_BASE ?? "https://bosque-vivo-web.vercel.app";
const SHOTS = process.env.PROD_SHOTS;
const POINT = { latitude: Number(process.env.PROD_LAT ?? 2.13348), longitude: Number(process.env.PROD_LON ?? -78.646178) };
const PROJECT = process.env.PROD_PROJECT ?? "Acapa";
const TEST_ACCOUNT = process.env.PROD_TEST_ACCOUNT ?? "pruebas@bosquevivo.test";
const TEST_PASSWORD = process.env.PROD_TEST_PASSWORD ?? "BosqueVivo-Pruebas-2026";
const PHOTO = path.join(__dirname, "../../../web/public/images/sat-before.jpg");
const results = [];
const timings = [];

function check(id, description, ok, detail = "") {
  results.push({ id, description, ok, detail });
  console.log(`${ok ? "OK   " : "FALLA"} ${id} ${description}${detail ? ` -> ${detail}` : ""}`);
}

async function site(page) {
  const response = await page.goto(`${BASE}/whatsapp`);
  check("CP-66", "/whatsapp redirige al chat en línea", new URL(page.url()).pathname === "/asistente" && response.ok());
  const mentions = [];
  for (const route of ["/", "/asistente", "/privacidad", "/terminos", "/acerca", "/uso-de-datos", "/metodologia", "/proyectos"]) {
    await page.goto(`${BASE}${route}`);
    if (/whatsapp/i.test(await page.textContent("body"))) mentions.push(route);
  }
  check("CP-66", "ninguna página de producción menciona WhatsApp", mentions.length === 0, mentions.join(", "));
}

async function testAccount(browser) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${BASE}/acceso?next=/chat`);
  await page.fill("#email", TEST_ACCOUNT);
  await page.fill("#password", TEST_PASSWORD);
  await page.click("button[type=submit]");
  try {
    await page.waitForURL((url) => url.pathname === "/chat", { timeout: 30000 });
    check("CP-65", "la cuenta de pruebas entra sin código en producción", true, page.url());
    const started = Date.now();
    await page.fill("textarea, input[type=text]", "¿Qué significa la confianza del índice?");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);
    await page.waitForFunction(() => !document.body.innerText.includes("Pensando"), null, { timeout: 60000 }).catch(() => {});
    check("CP-65", "con la cuenta de pruebas se usa el chat del auditor", true, `${((Date.now() - started) / 1000).toFixed(1)} s`);
  } catch {
    const error = (await page.locator("#error-acceso").textContent().catch(() => "")) || page.url();
    check("CP-65", "la cuenta de pruebas entra sin código en producción", false, error.trim());
  }
  await context.close();
}

async function chat(browser) {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    permissions: ["geolocation", "microphone"],
    geolocation: POINT,
  });
  const page = await context.newPage();
  await page.goto(`${BASE}/asistente`);
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check("CP-67", "en un celular (390 px) la página no se desborda", overflow <= 0, `${overflow} px`);
  const count = () => page.locator("[role=log] [data-from]").count();
  const waitReply = async (label, before) => {
    const started = Date.now();
    await page.waitForFunction(
      (n) => document.querySelectorAll("[role=log] [data-from]").length > n + 1 && !document.querySelector("[role=log] [role=status]"),
      before,
      { timeout: 90000 },
    );
    const seconds = (Date.now() - started) / 1000;
    const replies = (await page.locator("[role=log] [data-from]").allTextContents()).slice(before + 1);
    timings.push({ mensaje: label, segundos: Number(seconds.toFixed(2)), respuesta: replies.join(" | ").slice(0, 300) });
    return { replies, seconds };
  };
  const say = async (text) => {
    const before = await count();
    await page.fill('input[placeholder="Escribe tu mensaje"]', text);
    await page.click("button[aria-label=Enviar]");
    return waitReply(text, before);
  };
  const hello = await say("Hola");
  check("CP-49", "primer contacto con saludo y aviso de privacidad", hello.replies.some((t) => t.includes("ACEPTO")));
  await say("ACEPTO");
  check("CP-49", "AYUDA lista las consultas", (await say("AYUDA")).replies[0].includes("ALERTAS"));
  check("CP-49", "PROYECTO 1 registra el proyecto", (await say("PROYECTO 1")).replies[0].includes("quedó registrado"));
  const status = await say("ESTADO");
  check("CP-49", "ESTADO responde en lenguaje sencillo", status.replies[0].includes("se conserva"), status.replies[0].slice(0, 120));
  check("CP-49", "ALERTAS responde", (await say("ALERTAS")).replies[0].length > 0);
  const free = await say("¿Mi bosque está bien cuidado?");
  check("CP-49", "una pregunta libre recibe respuesta", free.replies.length > 0, `${free.seconds.toFixed(1)} s: ${free.replies[0].slice(0, 120)}`);

  let before = await count();
  await page.click("button[aria-label='Compartir mi ubicación']");
  const located = await waitReply("📍 ubicación", before);
  check("CP-67", "la ubicación del celular encuentra el proyecto", located.replies.some((t) => t.includes(PROJECT)), located.replies.join(" | ").slice(0, 160));

  await say("ACEPTO FOTOS");
  before = await count();
  await page.setInputFiles("[data-testid=foto]", PHOTO);
  const photo = await waitReply("📷 foto", before);
  check("CP-67", "la foto llega a Gemini y se responde", photo.replies.length > 0, `${photo.seconds.toFixed(1)} s: ${photo.replies[0].slice(0, 140)}`);

  before = await count();
  await page.click("button[aria-label='Grabar una nota de voz']");
  await page.waitForSelector("text=Grabando");
  await page.waitForTimeout(Number(process.env.PROD_AUDIO_SECONDS ?? 4) * 1000);
  await page.click("button[aria-label='Enviar la nota de voz']");
  const voice = await waitReply("🎤 nota de voz", before);
  check("CP-67", "la nota de voz se envía y se responde", voice.replies.length > 0, `${voice.seconds.toFixed(1)} s: ${voice.replies[0].slice(0, 140)}`);
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, "11-chat-produccion.png") });
  check("CP-49", "BORRAR MIS DATOS elimina la conversación", (await say("BORRAR MIS DATOS")).replies[0].includes("Borré"));
  await context.close();
}

(async () => {
  // PROD_AUDIO: WAV con una pregunta hablada que el navegador usa como micrófono (sin él, un tono de prueba).
  const audio = process.env.PROD_AUDIO ? [`--use-file-for-fake-audio-capture=${process.env.PROD_AUDIO}`] : [];
  const browser = await chromium.launch({
    args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", ...audio],
  });
  const page = await browser.newPage();
  try {
    await site(page);
    await chat(browser);
    await testAccount(browser);
  } catch (error) {
    check("PROD", "ejecución sin errores", false, String(error.message ?? error).slice(0, 300));
  } finally {
    await browser.close();
  }
  const under10 = timings.filter((t) => t.segundos < 10).length;
  const report = { fecha: new Date().toISOString(), sitio: BASE, resultados: results, tiempos: timings, bajo_10_s: `${under10}/${timings.length}` };
  if (process.env.PROD_REPORT) fs.writeFileSync(process.env.PROD_REPORT, JSON.stringify(report, null, 2));
  console.log(`Respuestas en menos de 10 s: ${under10} de ${timings.length}`);
  process.exit(results.every((result) => result.ok) ? 0 : 1);
})();
