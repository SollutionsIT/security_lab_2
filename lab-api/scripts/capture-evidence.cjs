/* Capture actual generated report sections; does not invent execution results. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '../..');
  const source = path.join(root, 'reports/portfolio/index.html');
  if (!fs.existsSync(source)) throw new Error('Run make portfolio-evidence first');
  const browser = await chromium.launch({
    ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}),
    headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 },
                                        deviceScaleFactor: 1 });
    await page.goto(pathToFileURL(source).href);
    await page.evaluate(() => document.fonts.ready);
    const output = path.join(root, 'docs/assets');
    fs.mkdirSync(output, { recursive: true });
    await page.locator('#overview').screenshot({ path: path.join(output, 'evidence-overview.png') });
    await page.locator('#demo').screenshot({ path: path.join(output, 'access-control-demo.png') });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    if (overflow) throw new Error('Report has horizontal overflow');
    console.log('Captured actual evidence sections in docs/assets; manually review before publishing.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
