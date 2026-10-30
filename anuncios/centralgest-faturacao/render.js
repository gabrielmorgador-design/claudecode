// Renderiza o anúncio em todos os formatos: node render.js
const path = require('path');
const { chromium } = require('playwright');

const formatos = [
  { f: '4x5', w: 1080, h: 1350, nome: 'centralgest_faturacao_1080x1350_v1' },
  { f: '1x1', w: 1080, h: 1080, nome: 'centralgest_faturacao_1080x1080_v1' },
  { f: '9x16', w: 1080, h: 1920, nome: 'centralgest_faturacao_1080x1920_v1' },
  { f: 'li', w: 1200, h: 627, nome: 'centralgest_faturacao_1200x627_v1' },
  { f: 'b', w: 1080, h: 1350, nome: 'centralgest_faturacao_1080x1350_v1-B' },
];

(async () => {
  const browser = await chromium.launch();
  const html = 'file://' + path.join(__dirname, 'anuncio.html');
  for (const { f, w, h, nome } of formatos) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.goto(`${html}?f=${f}`);
    await page.evaluate(() => document.fonts.ready);
    // Avisa se alguma linha de texto sair da margem.
    const excesso = await page.evaluate((w) => [...document.querySelectorAll('.titulo > span, .apoio > span')]
      .filter(s => { const r = document.createRange(); r.selectNodeContents(s); return r.getBoundingClientRect().right > w - 56; })
      .map(s => s.textContent), w);
    if (excesso.length) console.warn(`${nome}: texto fora da margem ->`, excesso);
    await page.screenshot({ path: path.join(__dirname, 'export', `${nome}.png`) });
    await page.close();
    console.log('ok', nome);
  }
  await browser.close();
})();
