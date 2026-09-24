#!/usr/bin/env node
// Скриншоты прототипов раунда: headless Chromium, 1440×900 и 1920×1080.
//
//   node tools/shots.mjs rounds/01-foo [rounds/01-bar ...]
//
// Для каждой папки открывает index.html как file:// и снимает каждое состояние
// из необязательного shots.json: [{ "name": "main" }, { "name": "health", "hash": "#health" }].
// Без shots.json — одно состояние "main". Результат: <папка>/shots/<name>-<W>x<H>.png.
//
// Сеть запрещена: любой запрос не к file:// обрывается и печатается — так
// ловится случайный CDN или внешний шрифт (прототипы обязаны быть самодостаточными).
// Анимации на снимке выключены. Ошибки консоли страницы печатаются.
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
function loadPlaywright() {
  try { return require('playwright'); } catch { /* нет локального — берём глобальный */ }
  const globalRoot = execSync('npm root -g').toString().trim();
  return require(path.join(globalRoot, 'playwright'));
}

const SIZES = [[1440, 900], [1920, 1080]];
const dirs = process.argv.slice(2);
if (!dirs.length) {
  console.error('usage: node tools/shots.mjs <round-dir> [...]');
  process.exit(2);
}

const { chromium } = loadPlaywright();
const browser = await chromium.launch();
let problems = 0;

for (const dir of dirs) {
  const index = path.resolve(dir, 'index.html');
  if (!fs.existsSync(index)) {
    console.error(`✖ ${dir}: нет index.html`);
    problems++;
    continue;
  }
  const specPath = path.resolve(dir, 'shots.json');
  const states = fs.existsSync(specPath)
    ? JSON.parse(fs.readFileSync(specPath, 'utf8'))
    : [{ name: 'main' }];
  const outDir = path.resolve(dir, 'shots');
  fs.mkdirSync(outDir, { recursive: true });

  for (const [width, height] of SIZES) {
    const context = await browser.newContext({
      viewport: { width, height },
      deviceScaleFactor: 1,
      colorScheme: 'dark',
      locale: 'ru-RU',
    });
    await context.route('**/*', (route) => {
      const url = route.request().url();
      if (url.startsWith('file:') || url.startsWith('data:')) return route.continue();
      console.error(`✖ ${dir}: сетевой запрос заблокирован — ${url}`);
      problems++;
      return route.abort();
    });
    const page = await context.newPage();
    page.on('console', (msg) => {
      // ERR_FAILED — эхо нашего же блока сети, он уже напечатан выше.
      if (msg.type() !== 'error' || msg.text().includes('net::ERR_FAILED')) return;
      console.error(`✖ ${dir} console: ${msg.text()}`);
      problems++;
    });
    page.on('pageerror', (err) => { console.error(`✖ ${dir} pageerror: ${err.message}`); problems++; });

    for (const state of states) {
      const url = pathToFileURL(index).href + (state.hash || '');
      await page.goto(url, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const file = path.join(outDir, `${state.name}-${width}x${height}.png`);
      await page.screenshot({ path: file, animations: 'disabled' });
      console.log(`✓ ${path.relative(process.cwd(), file)}`);
    }
    await context.close();
  }
}

await browser.close();
process.exit(problems ? 1 : 0);
