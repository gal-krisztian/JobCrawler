import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


EMAIL_ADDRESS = "gywellin@proton.me"


def create_browser_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=hu-HU")
    options.add_argument("--accept-lang=hu-HU,hu;q=0.9,en;q=0.8")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
    return options


async def find_login_button(tab):
    login_texts = ["Bejelentkezés", "Belépés", "Sign in", "Log in"]

    for text in login_texts:
        try:
            return await tab.find(tag_name="a", text=text)
        except Exception:
            pass

    selectors = [
        'a[href*="account"]',
        'a[href*="login"]',
        'a[href*="signin"]',
        'a[aria-label*="Bejelentkez"]',
    ]

    for selector in selectors:
        try:
            return await tab.find(css_selector=selector)
        except Exception:
            pass

    raise RuntimeError("Nem található bejelentkezési gomb vagy link az oldalon.")


async def find_email_field(tab):
    selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[id*="email"]',
        'input[autocomplete="email"]',
    ]

    for selector in selectors:
        try:
            return await tab.find(css_selector=selector)
        except Exception:
            pass

    raise RuntimeError("Nem található e-mail cím mező a bejelentkezési oldalon.")


async def find_continue_button(tab):
    button_texts = ["Tovább", "Continue", "Folytatás", "Next"]

    for text in button_texts:
        try:
            return await tab.find(tag_name="button", text=text)
        except Exception:
            pass

    try:
        return await tab.find(tag_name="button", type="submit")
    except Exception as exc:
        raise RuntimeError("Nem található a Tovább gomb.") from exc


async def main():
    async with Chrome(options=create_browser_options()) as browser:
        tab = await browser.start()
        await tab.go_to("https://hu.indeed.com")
        await asyncio.sleep(3)

        login_button = await find_login_button(tab)
        await login_button.click()

        print("A bejelentkezési oldal megnyitva.")
        await asyncio.sleep(3)

        email_field = await find_email_field(tab)
        await email_field.type_text(EMAIL_ADDRESS)

        continue_button = await find_continue_button(tab)
        await continue_button.click()

        print("Az e-mail cím megadva, a Tovább gomb megnyomva.")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
