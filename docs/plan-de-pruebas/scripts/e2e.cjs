const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.E2E_BASE ?? "http://localhost:3100";
const OUTBOX = process.env.E2E_OUTBOX;
const SHOTS = process.env.E2E_SHOTS;
const EMAIL = process.env.E2E_EMAIL ?? "auditora@elpoli.edu.co";
const NEW_PASSWORD = "NuevaClave2026";
const results = [];

function check(id, description, ok, detail = "") {
  results.push({ id, description, ok, detail });
  console.log(`${ok ? "OK   " : "FALLA"} ${id} ${description}${detail ? ` -> ${detail}` : ""}`);
}

async function shot(page, name) {
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, name), fullPage: false });
}

function latestLink() {
  const file = fs.readdirSync(OUTBOX).filter((f) => f.endsWith(".eml")).sort().pop();
  const raw = fs.readFileSync(path.join(OUTBOX, file), "utf8").replace(/=\r?\n/g, "").replace(/=3D/g, "=");
  const match = raw.match(/https?:\/\/\S+\/acceso\/restablecer\?token=[\w-]+/);
  return match ? match[0] : null;
}

async function rf09(page) {
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
  check("CP-36", "la contraseña se actualiza", (await page.textContent("main [role=status]")).includes("se actualizó"));
  await shot(page, "05-confirmacion.png");

  await page.goto(link);
  check("CP-34", "el enlace ya usado se rechaza", (await page.textContent("main [role=alert]")).includes("ya se usó"));

  await page.goto(`${BASE}/acceso?next=/trazas`);
  await page.fill("#email", EMAIL);
  await page.fill("#password", NEW_PASSWORD);
  await page.click("button[type=submit]");
  await page.waitForURL((url) => url.pathname === "/trazas", { timeout: 60000 });
  check("CP-37", "inicio de sesión con la contraseña nueva", true, page.url());
  await page.goto(`${BASE}/acceso`);
  check("CP-37", "la sesión muestra el correo del auditor", (await page.textContent("main form")).includes(EMAIL));
  await shot(page, "06-sesion.png");
}

async function chat(page) {
  try {
    await page.evaluate(() => window.localStorage.clear());
  } catch {}
  await page.goto(`${BASE}/asistente`);
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
  check("CP-21", "primer contacto: saludo y aviso de privacidad", hello.length === 2 && hello[1].includes("ACEPTO"), JSON.stringify(hello));
  check("CP-22", "sin autorización no responde consultas", (await say("estado"))[0].includes("ACEPTO"));
  await say("ACEPTO");
  check("CP-23", "AYUDA lista las consultas disponibles", (await say("AYUDA"))[0].includes("ALERTAS"));
  check("CP-24", "PROYECTO <n> registra el polígono de interés", (await say("proyecto 1"))[0].includes("quedó registrado"));
  const status = (await say("estado"))[0];
  check("CP-27", "ESTADO responde en lenguaje sencillo con el % conservado", status.includes("se conserva el"), status);
  check("CP-28", "sin términos técnicos ni acusaciones", !/fraude|ndvi|redd|índice/i.test(status));
  check("CP-25", "ALERTAS responde para el proyecto", (await say("alertas"))[0].includes("Reserva El Roble"));
  const unknown = await say("¿qué tiempo hará mañana?");
  check("CP-26", "consulta no reconocida orienta con la ayuda", unknown.some((t) => t.includes("ESTADO")));
  await shot(page, "07-chat-en-linea.png");
  check("CP-42", "BORRAR MIS DATOS elimina la conversación", (await say("BORRAR MIS DATOS"))[0].includes("Borré"));
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  try {
    await rf09(page);
    await chat(page);
  } catch (error) {
    check("E2E", "ejecución sin errores", false, String(error.message ?? error));
  } finally {
    await browser.close();
  }
  if (process.env.E2E_REPORT) fs.writeFileSync(process.env.E2E_REPORT, JSON.stringify(results, null, 2));
  process.exit(results.every((r) => r.ok) ? 0 : 1);
})();
