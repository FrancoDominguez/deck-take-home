import pytest
import json
from playwright.async_api import async_playwright
from jsonschema import validate, ValidationError
from src.scraper import login, accept_cookies, scrape


schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "account name": {"type": "string"},
            "account number": {"type": "string"},
            "last month usage": {"type": "string"},
            "due date": {"type": "string"},
            "current balance": {"type": "string"},
            "latest bill": {"type": "string"},
            "statements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "statement date": {"type": "string"},
                        "amount": {"type": "string"},
                        "usage": {"type": "string"},
                        "download path": {"type": "string"}
                    },
                    "required": ["statement date","amount","usage","download path"]
                }
            }
        },
        "required": [
            "account name",
            "account number",
            "last month usage",
            "due date",
            "current balance"
        ]
    }
}

@pytest.mark.asyncio
async def test_confirm_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://deck-dev-eastus2-academy.yellowrock-2749f805.eastus2.azurecontainerapps.io/mfa-login")
        await accept_cookies(page)
        await login(page)
        logout_button = page.locator("text=Logout")
        assert await logout_button.is_visible()
        await browser.close()

@pytest.mark.asyncio
async def test_validate_json():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://deck-dev-eastus2-academy.yellowrock-2749f805.eastus2.azurecontainerapps.io/mfa-login")
        await scrape(page)
        await browser.close()

    with open("./output/data.json") as f:
        data = json.load(f)

    validate(instance=data, schema=schema)



