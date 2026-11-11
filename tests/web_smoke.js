// Open the web build in headless Chrome: the engine must start without a
// page error, and a click on the document must open the reading view.
//   python3 -m http.server 8060 -d build/web &
//   npm install puppeteer-core && node tests/web_smoke.js [chrome path]
// Writes web_masa.png and web_okuma.png into the folder named by SHOTS (default: here).
const puppeteer = require('puppeteer-core');
const path = require('path');

(async () => {
  const out = process.env.SHOTS || '.';
  const browser = await puppeteer.launch({
    executablePath: process.argv[2] || '/usr/bin/google-chrome',
    headless: 'new',
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--window-size=1280,720'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('requestfailed', r => errors.push('request failed: ' + r.url()));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const t0 = Date.now();
  await page.goto('http://localhost:8060/index.html', { waitUntil: 'load', timeout: 120000 });
  let started = false;
  for (let i = 0; i < 120 && !started; i++) {
    await new Promise(r => setTimeout(r, 1000));
    started = await page.evaluate(() => { const s = document.getElementById('status'); return !s || s.offsetParent === null; });
  }
  console.log(`engine started: ${started}, ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({ path: path.join(out, 'web_masa.png') });
  await page.mouse.click(487, 367);           // an empty spot on the document: opens the reading view
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(out, 'web_okuma.png') });
  await browser.close();
  if (!started || errors.length) {
    console.error('FAILED', errors);
    process.exit(1);
  }
  console.log('ok');
})();
