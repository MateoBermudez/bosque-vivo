const { chromium } = require("playwright");
const path = require("path");

(async () => {
  const [input, output] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`file://${path.resolve(input)}`, { waitUntil: "load" });
  await page.pdf({
    path: output,
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size:7pt;width:100%;text-align:right;padding:0 16mm;color:#5b6b5f">Bosque Vivo · Plan de Pruebas de Software</div>',
    footerTemplate: '<div style="font-size:7pt;width:100%;text-align:center;color:#5b6b5f"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    margin: { top: "18mm", bottom: "20mm", left: "16mm", right: "16mm" },
  });
  await browser.close();
})();
