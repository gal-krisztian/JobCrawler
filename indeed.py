import asyncio
import json
from pathlib import Path
from httpx import options
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

cookies_file = Path("./Files/indeed_cookies.json")

def create_browser_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=hu-HU")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
    return options

async def main():
    start_url = "https://hu.indeed.com"
    search_location = ["Pest"]

    async with Chrome(options=create_browser_options()) as browser:
        tab = await browser.start()
        await tab.go_to(start_url)
        await asyncio.sleep(3)

        login_button = await tab.find(tag_name="a", text="Bejelentkezés")
        await login_button.click()

        await asyncio.sleep(3)

        location_textbox = await tab.find(tag_name="input", type="email")
        await location_textbox.type_text("gywellin@proton.me")

        await asyncio.sleep(3)

        submit_button = await tab.find(tag_name="button", type="submit")
        await submit_button.click()

        """location_textbox = await tab.find(id="text-input-where")
        await location_textbox.type_text(search_location[0])
        submit_button = await tab.find(tag_name="button", type="submit")
        await submit_button.click()

        job_cards = await tab.find(tag_name="a", find_all=True) """

        await asyncio.sleep(10)

        print("Done.")

asyncio.run(main())