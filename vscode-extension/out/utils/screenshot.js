"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.captureScreenshot = captureScreenshot;
const playwright_1 = require("playwright");
async function captureScreenshot(url, savePath) {
    const browser = await playwright_1.chromium.launch();
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.screenshot({ path: savePath, fullPage: true });
    await browser.close();
}
//# sourceMappingURL=screenshot.js.map