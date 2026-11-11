// Renders an HTML motion page frame by frame and encodes it to MP4 (H.264, 30 fps).
// Usage: node render.js <page.html> <out.mp4> [seconds=10] [--preview t1,t2,...]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

(async () => {
  const [page, out, secArg, flag, list] = process.argv.slice(2);
  const secs = Number(secArg || 10), fps = 30;
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const browser = await chromium.launch({ proxy });
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1920 }, ignoreHTTPSErrors: true });
  const p = await ctx.newPage();
  await p.goto('file://' + path.resolve(page));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  const shoot = async (ms, file) => { await p.evaluate(t => window.seek(t), ms); await p.screenshot({ path: file, clip: { x: 0, y: 0, width: 1080, height: 1920 } }); };

  if (flag === '--preview') {
    for (const t of list.split(',')) await shoot(Number(t) * 1000, `${out}_${t}s.png`);
  } else {
    const dir = fs.mkdtempSync(path.join(path.dirname(path.resolve(out)), '.frames-'));
    const n = Math.round(secs * fps);
    for (let i = 0; i < n; i++) await shoot((i * 1000) / fps, path.join(dir, String(i).padStart(4, '0') + '.png'));
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(dir, '%04d.png'),
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart', out]);
    for (const f of fs.readdirSync(dir)) fs.unlinkSync(path.join(dir, f));
    fs.rmdirSync(dir);
  }
  await browser.close();
})();
