#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8799"
ADMIN_PASSWORD = "admin123"
USER_PASSWORD = "test123"


async def add_space(page, name, desc=""):
    return await page.evaluate(f"""async () => {{
        const fd = new FormData();
        fd.append('name', '{name}');
        fd.append('description', '{desc}');
        const r = await fetch('/admin/spaces/add', {{method:'POST', body:fd}});
        return r.status;
    }}""")


async def goto_wait(page, url):
    await page.goto(url)
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(3000)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        seed = await browser.new_page()
        await seed.goto(f"{BASE}/login")
        await seed.wait_for_selector("input[name=username]")
        await seed.fill("input[name=username]", "Admin")
        await seed.fill("input[name=password]", ADMIN_PASSWORD)
        await seed.click("button[type=submit]")
        await seed.wait_for_load_state("networkidle")
        for name, desc in [("A1", "Near entrance"), ("A2", ""), ("B1", "Ground floor"), ("Visitor", "")]:
            r = await add_space(seed, name, desc)
            print(f"  Space {name}: {r}")
        await seed.close()

        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await goto_wait(page, f"{BASE}/login")
        await page.screenshot(path="screenshots/login.png")
        print("Saved login.png")

        await page.fill("input[name=username]", "Jan Kowalski")
        await page.fill("input[name=password]", USER_PASSWORD)
        await page.click("button[type=submit]")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="screenshots/index.png")
        print("Saved index.png")

        try:
            btn = page.locator("button").filter(has_text="Reserve").first
            await btn.wait_for(state="visible", timeout=4000)
            await btn.click()
            await page.wait_for_timeout(700)
            await page.screenshot(path="screenshots/reserve_modal.png")
            print("Saved reserve_modal.png")
        except Exception as e:
            print(f"  Modal skip: {e}")

        await page.evaluate("() => fetch('/logout', {method:'POST'})")
        await page.wait_for_timeout(300)
        await goto_wait(page, f"{BASE}/login")
        await page.fill("input[name=username]", "Admin")
        await page.fill("input[name=password]", ADMIN_PASSWORD)
        await page.click("button[type=submit]")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(3000)
        await goto_wait(page, f"{BASE}/admin")
        await page.screenshot(path="screenshots/admin.png", full_page=True)
        print("Saved admin.png")

        await browser.close()

asyncio.run(main())
