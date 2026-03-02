#!/usr/bin/env python3
"""Take screenshots of mockup HTML files using Playwright."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

MOCKUPS = [
    ("login_mockup.html", "login.png", 1280, 800),
    ("index_mockup.html", "index.png", 1440, 900),
    ("admin_mockup.html", "admin.png", 1440, 1100),
]

async def main():
    base = Path(__file__).parent
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for html_file, out_file, width, height in MOCKUPS:
            page = await browser.new_page(viewport={"width": width, "height": height})
            path = (base / html_file).resolve()
            await page.goto(f"file://{path}")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(base / out_file), full_page=False)
            print(f"  Saved {out_file}")
        await browser.close()

asyncio.run(main())
