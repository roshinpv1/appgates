import { chromium } from 'playwright';

export async function captureScreenshot(url: string, savePath: string) {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.screenshot({ path: savePath, fullPage: true });
    await browser.close();
} 