const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.E2E_BASE ?? "http://localhost:3100";
const OUTBOX = process.env.E2E_OUTBOX;
const SHOTS = process.env.E2E_SHOTS;
const EMAIL = process.env.E2E_EMAIL ?? "auditora@elpoli.edu.co";
const INITIAL_PASSWORD = "BosqueVivo2026";
const NEW_PASSWORD = "NuevaClave2026";
const results = [];

function check(id, description, ok, detail = "") {
  results.push({ id, description, ok, detail });
  console.log(`${ok ? "OK   " : "FALLA"} ${id} ${description}${detail ? ` -> ${detail}` : ""}`);
}

async function shot(page, name) {
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, name), fullPage: false });
}

function decodeQuotedPrintable(text) {
  const joined = text.replace(/=\r?\n/g, "");
  const bytes = [];
  for (let i = 0; i < joined.length; i++) {
    const hex = joined.slice(i + 1, i + 3);
    if (joined[i] === "=" && /^[0-9A-F]{2}$/.test(hex)) {
      bytes.push(parseInt(hex, 16));
      i += 2;
    } else {
      bytes.push(...Buffer.from(joined[i], "utf8"));
    }
  }
  return Buffer.from(bytes).toString("utf8");
}

function mails() {
  return fs
    .readdirSync(OUTBOX)
    .filter((file) => file.endsWith(".eml"))
    .sort()
    .map((file) => decodeQuotedPrintable(fs.readFileSync(path.join(OUTBOX, file), "utf8")));
}

function latest(pattern) {
  for (const mail of mails().reverse()) {
    const match = mail.match(pattern);
    if (match) return match;
  }
  return null;
}

const latestLink = () => latest(/https?:\/\/\S+\/acceso\/restablecer\?token=[\w-]+/)?.[0] ?? null;
const latestCode = () => latest(/Código: (\d{6})/)?.[1] ?? null;

async function invitation(page) {
  const link = latestLink();
  const invited = mails().some((mail) => mail.includes("Se creó una cuenta de auditor"));
  check("CP-56", "la invitación llega con un enlace para activar la cuenta", Boolean(link) && invited);
  await page.goto(link);
  await page.waitForSelector("#password");
  check("CP-56", "la página de la invitación da la bienvenida", (await page.textContent("main")).includes("Bienvenido al área de auditores"));
  await page.fill("#password", INITIAL_PASSWORD);
  await page.fill("#confirmacion", INITIAL_PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForSelector("main [role=status]");
  check("CP-56", "la cuenta queda activa con la contraseña elegida", (await page.textContent("main [role=status]")).includes("quedó guardada"));
  await shot(page, "00-invitacion-activada.png");
}

async function recovery(page) {
  await page.goto(`${BASE}/chat`);
  check("CP-30", "el área de auditores redirige a /acceso", new URL(page.url()).pathname === "/acceso");
  await page.fill("#email", EMAIL);
  await page.fill("#password", "incorrecta123");
  await page.click("button[type=submit]");
  await page.waitForSelector("#error-acceso");
  check("CP-31", "credenciales inválidas muestran error", (await page.textContent("#error-acceso")).includes("no son correctos"));
  await shot(page, "01-login-error.png");

  await page.click("text=¿Olvidaste tu contraseña?");
  await page.waitForURL("**/acceso/recuperar");
  await page.fill("#email", "noexiste@elpoli.edu.co");
  await page.click("button[type=submit]");
  const unknown = await page.textContent("main [role=status]");
  await page.goto(`${BASE}/acceso/recuperar`);
  await page.fill("#email", EMAIL);
  await page.click("button[type=submit]");
  const known = await page.textContent("main [role=status]");
  check("CP-32", "mismo mensaje genérico para correo registrado y no registrado", unknown === known, known);
  await shot(page, "02-recuperar-enviado.png");

  const link = latestLink();
  check("CP-33", "el correo contiene un enlace de restablecimiento", Boolean(link));

  await page.goto(`${BASE}/acceso/restablecer?token=falso`);
  check("CP-34", "un token inválido se rechaza", (await page.textContent("main [role=alert]")).includes("no es válido"));
  await shot(page, "03-token-invalido.png");

  await page.goto(link);
  await page.fill("#password", NEW_PASSWORD);
  await page.fill("#confirmacion", "OtraClave2026");
  await page.click("button[type=submit]");
  await page.waitForSelector("main [role=alert]");
  check("CP-35", "contraseñas distintas se rechazan", (await page.textContent("main [role=alert]")).includes("no coinciden"));
  await page.fill("#password", "soloLetrasSinNumero");
  await page.fill("#confirmacion", "soloLetrasSinNumero");
  await page.click("button[type=submit]");
  await page.waitForFunction(() => document.querySelector("main [role=alert]")?.textContent?.includes("letra y un número"));
  check("CP-35", "contraseña débil se rechaza", true);
  await page.fill("#password", NEW_PASSWORD);
  await page.fill("#confirmacion", NEW_PASSWORD);
  await shot(page, "04-restablecer.png");
  await page.click("button[type=submit]");
  await page.waitForSelector("main [role=status]");
  check("CP-36", "la contraseña se actualiza", (await page.textContent("main [role=status]")).includes("quedó guardada"));
  await shot(page, "05-confirmacion.png");

  await page.goto(link);
  check("CP-34", "el enlace ya usado se rechaza", (await page.textContent("main [role=alert]")).includes("ya se usó"));
}

async function twoFactor(page) {
  await page.goto(`${BASE}/acceso?next=/trazas`);
  await page.fill("#email", EMAIL);
  await page.fill("#password", NEW_PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForSelector("#codigo-verificacion");
  check("CP-53", "después de la contraseña se pide el código enviado por correo", (await page.textContent("main form")).includes("Lo enviamos a"));
  await shot(page, "08-codigo-2fa.png");
  const real = latestCode();
  check("CP-53", "el correo contiene un código de 6 dígitos", Boolean(real));
  await page.fill("#codigo-verificacion", real === "000000" ? "111111" : "000000");
  await page.click("button[value=verificar]");
  await page.waitForSelector("#error-acceso");
  check("CP-54", "un código incorrecto se rechaza", (await page.textContent("#error-acceso")).includes("no es correcto"));
  const before = mails().length;
  await page.click("button[value=reenviar]");
  await page.waitForFunction(() => document.querySelector("main [role=status]")?.textContent?.includes("código nuevo"));
  check("CP-54", "se puede reenviar el código", mails().length === before + 1);
  await page.fill("#codigo-verificacion", latestCode());
  await page.click("button[value=verificar]");
  await page.waitForURL((url) => url.pathname === "/trazas", { timeout: 60000 });
  check("CP-37", "con la contraseña nueva y el código se entra al área de auditores", true, page.url());
  await page.goto(`${BASE}/acceso`);
  check("CP-37", "la sesión muestra el correo del auditor", (await page.textContent("main form")).includes(EMAIL));
  await shot(page, "06-sesion.png");
  const all = mails();
  check("CP-55", "llega el aviso de nuevo inicio de sesión", all.some((mail) => mail.includes("Se inició sesión en tu cuenta")));
  check("CP-55", "llega el aviso de cambio de contraseña", all.some((mail) => mail.includes("se cambió el")));
  check("CP-55", "los correos tienen versión HTML", all.every((mail) => mail.includes("text/html")));
  check(
    "CP-64",
    "los correos llevan el diseño de la marca y enlaces a privacidad y términos",
    all.every((mail) => mail.includes("Auditoría satelital de carbono forestal") && mail.includes(`${BASE}/privacidad`) && mail.includes(`${BASE}/terminos`)),
  );
}

async function legal(page) {
  const pages = [
    ["/terminos", "Términos y condiciones", ["Alcance de los resultados", "Uso aceptable", "República de Colombia"]],
    ["/privacidad", "Política de privacidad y tratamiento de datos", ["Responsable del tratamiento", "10 días hábiles", "15 días hábiles", "BORRAR MIS DATOS", "Superintendencia de Industria y Comercio"]],
    ["/uso-de-datos", "Uso de datos y fuentes", ["CC BY 4.0", "Karnik", "Hansen", "Limitaciones y descargo"]],
  ];
  for (const [route, title, phrases] of pages) {
    const response = await page.goto(`${BASE}${route}`);
    const text = await page.textContent("main");
    const missing = phrases.filter((phrase) => !text.includes(phrase));
    check(
      "CP-63",
      `${route} publica «${title}» con versión y fecha`,
      response.status() === 200 && (await page.textContent("h1")).includes(title) && /Versión v\d/.test(text) && missing.length === 0,
      missing.join(", "),
    );
  }
  await shot(page, "09-uso-de-datos.png");
  const footer = await page.locator("footer a").evaluateAll((links) => links.map((link) => link.getAttribute("href")));
  check("CP-63", "el pie enlaza los tres documentos legales", ["/terminos", "/privacidad", "/uso-de-datos"].every((href) => footer.includes(href)));
  await page.goto(`${BASE}/asistente`);
  const notice = await page.locator("main a").evaluateAll((links) => links.map((link) => link.getAttribute("href")));
  check("CP-63", "el chat en línea remite a la política y a los términos", notice.includes("/privacidad") && notice.includes("/terminos"));
}

async function chat(page) {
  await page.goto(`${BASE}/asistente`);
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  const say = async (text) => {
    const before = await page.locator("[role=log] [data-from]").count();
    await page.fill('input[placeholder="Escribe tu mensaje"]', text);
    await page.click("button[aria-label=Enviar]");
    await page.waitForFunction(
      (n) => document.querySelectorAll("[role=log] [data-from]").length > n + 1 && !document.querySelector("[role=log] [role=status]"),
      before,
      { timeout: 60000 },
    );
    const all = await page.locator("[role=log] [data-from]").allTextContents();
    return all.slice(before + 1);
  };
  const hello = await say("Hola");
  check("CP-21", "primer contacto: saludo y aviso de privacidad", hello.length === 2 && hello[1].includes("ACEPTO"));
  check("CP-22", "sin autorización no responde consultas", (await say("estado"))[0].includes("ACEPTO"));
  await say("ACEPTO");
  check("CP-23", "AYUDA lista las consultas disponibles", (await say("AYUDA"))[0].includes("ALERTAS"));
  check("CP-24", "PROYECTO <n> registra el polígono de interés", (await say("proyecto 1"))[0].includes("quedó registrado"));
  const status = (await say("estado"))[0];
  check("CP-27", "ESTADO responde en lenguaje sencillo con el % conservado", status.includes("se conserva el"), status);
  check("CP-28", "sin términos técnicos ni acusaciones", !/fraude|ndvi|redd|índice/i.test(status));
  check("CP-25", "ALERTAS responde para el proyecto", (await say("alertas"))[0].includes("Reserva El Roble"));
  const unknown = await say("¿qué tiempo hará mañana?");
  check("CP-26", "consulta no reconocida orienta con la ayuda", unknown.some((text) => text.includes("ESTADO")));
  await shot(page, "07-chat-en-linea.png");
  check("CP-42", "BORRAR MIS DATOS elimina la conversación", (await say("BORRAR MIS DATOS"))[0].includes("Borré"));
}

const TEST_ACCOUNT = "pruebas@bosquevivo.test";
const TEST_PASSWORD = "BosqueVivo-Pruebas-2026";

async function testAccount(browser) {
  const context = await browser.newContext({ viewport: { width: 1100, height: 900 } });
  const page = await context.newPage();
  const before = mails().length;
  await page.goto(`${BASE}/acceso?next=/chat`);
  await page.fill("#email", TEST_ACCOUNT);
  await page.fill("#password", TEST_PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL((url) => url.pathname === "/chat", { timeout: 60000 });
  check("CP-65", "la cuenta de pruebas compartida entra sin código de verificación", true, page.url());
  check("CP-65", "la cuenta de pruebas no recibe correos de aviso", mails().length === before);
  await page.goto(`${BASE}/acceso`);
  check("CP-65", "la sesión muestra la cuenta de pruebas", (await page.textContent("main form")).includes(TEST_ACCOUNT));
  await context.close();
}

async function noWhatsApp(page) {
  const response = await page.goto(`${BASE}/whatsapp`);
  check("CP-66", "/whatsapp redirige al chat en línea", new URL(page.url()).pathname === "/asistente" && response.ok());
  const routes = ["/", "/asistente", "/privacidad", "/terminos", "/acerca", "/uso-de-datos", "/metodologia"];
  const mentions = [];
  for (const route of routes) {
    await page.goto(`${BASE}${route}`);
    if (/whatsapp/i.test(await page.textContent("body"))) mentions.push(route);
  }
  check("CP-66", "ninguna página del sitio menciona WhatsApp", mentions.length === 0, mentions.join(", "));
  const nav = await page.locator("header a").evaluateAll((links) => links.map((link) => link.getAttribute("href")));
  check("CP-66", "el menú lleva al asistente en /asistente", nav.includes("/asistente") && !nav.includes("/whatsapp"));
}

async function chatMedia(browser) {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    permissions: ["geolocation", "microphone"],
    geolocation: { latitude: 6.2, longitude: -75.6 },
  });
  const page = await context.newPage();
  await page.goto(`${BASE}/asistente`);
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check("CP-67", "en un celular (390 px) la página no se desborda a lo ancho", overflow <= 0, `${overflow} px`);
  const count = () => page.locator("[role=log] [data-from]").count();
  const waitReply = async (before) => {
    await page.waitForFunction(
      (n) => document.querySelectorAll("[role=log] [data-from]").length > n + 1 && !document.querySelector("[role=log] [role=status]"),
      before,
      { timeout: 90000 },
    );
    return (await page.locator("[role=log] [data-from]").allTextContents()).slice(before);
  };
  const say = async (text) => {
    const before = await count();
    await page.fill('input[placeholder="Escribe tu mensaje"]', text);
    await page.click("button[aria-label=Enviar]");
    return (await waitReply(before)).slice(1);
  };
  await say("Hola");
  await say("ACEPTO");
  let before = await count();
  await page.click("button[aria-label='Compartir mi ubicación']");
  const located = await waitReply(before);
  check("CP-67", "compartir la ubicación desde el celular encuentra el proyecto", located[0].includes("Ubicación compartida") && located.slice(1).some((text) => text.includes("Reserva El Roble")), located.join(" | "));
  before = await count();
  await page.setInputFiles("[data-testid=foto]", path.join(__dirname, "../../../web/public/images/sat-before.jpg"));
  const photoWithout = await waitReply(before);
  check("CP-67", "una foto sin permiso aparte pide ACEPTO FOTOS", photoWithout.slice(1).some((text) => text.includes("ACEPTO FOTOS")));
  await say("ACEPTO FOTOS");
  before = await count();
  await page.setInputFiles("[data-testid=foto]", path.join(__dirname, "../../../web/public/images/sat-before.jpg"));
  const photo = await waitReply(before);
  check("CP-67", "la foto se envía y el asistente responde", Boolean(await page.locator("[role=log] img[alt='Foto enviada']").count()) && photo.length >= 2, photo.slice(1).join(" | "));
  before = await count();
  await page.click("button[aria-label='Grabar una nota de voz']");
  await page.waitForSelector("text=Grabando");
  await page.waitForTimeout(2500);
  await page.click("button[aria-label='Enviar la nota de voz']");
  const voice = await waitReply(before);
  check("CP-67", "la nota de voz se graba, se envía y el asistente responde", voice[0].includes("Nota de voz") && voice.length >= 2, voice.join(" | "));
  await shot(page, "10-chat-celular.png");
  check("CP-42", "BORRAR MIS DATOS elimina la conversación", (await say("BORRAR MIS DATOS"))[0].includes("Borré"));
  await context.close();
}

(async () => {
  const browser = await chromium.launch({ args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"] });
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  try {
    await invitation(page);
    await recovery(page);
    await twoFactor(page);
    await chat(page);
    await legal(page);
    await testAccount(browser);
    await noWhatsApp(page);
    await chatMedia(browser);
  } catch (error) {
    check("E2E", "ejecución sin errores", false, String(error.message ?? error));
  } finally {
    await browser.close();
  }
  if (process.env.E2E_REPORT) fs.writeFileSync(process.env.E2E_REPORT, JSON.stringify(results, null, 2));
  process.exit(results.every((result) => result.ok) ? 0 : 1);
})();
