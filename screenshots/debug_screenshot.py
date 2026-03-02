#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8767"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # Login
        await page.goto(f"{BASE}/login")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(3000)

        print("Login page title:", await page.title())
        print("Login page URL:", page.url)

        await page.fill("input[name=username]", "Jan Kowalski")
        await page.fill("input[name=password]", "test123")
        await page.click("button[type=submit]")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(3000)

        print("After login URL:", page.url)
        print("After login title:", await page.title())

        # Get page text
        body_text = await page.inner_text("body")
        print("Body text (first 500):", body_text[:500])

        # Check style count
        style_count = await page.evaluate("() => document.querySelectorAll('style').length")
        print("Style tags:", style_count)

        await page.screenshot(path="/config/workspace/parking/screenshots/debug_index.png", full_page=True)
        print("Saved debug_index.png")

        await browser.close()

asyncio.run(main())
