import pytest
import json
import os
import shutil
from playwright.async_api import async_playwright
from jsonschema import validate
from src.scraper import login, accept_cookies, scrape

# not the cleanest way I could've handled a separate output folder for tests but it does for now
test_output_path = "./output.tests"

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

def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        return
    for item in os.listdir(folder_path):
        path = os.path.join(folder_path, item)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

@pytest.mark.asyncio
async def test_confirm_login():
    """
    Verifies the user is logged in by expecting a logout button to be visisble
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://deck-dev-eastus2-academy.yellowrock-2749f805.eastus2.azurecontainerapps.io/mfa-login")

        await accept_cookies(page)
        await login(page)

        logout_button = page.locator("text=Logout")
        assert await logout_button.is_visible()
        await browser.close()

@pytest.mark.asyncio
async def test_validate_json():
    """
    Verifies the extracted json format is correct and that the files were successfully downloaded
    """
    async with async_playwright() as p:
        clear_folder(test_output_path)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://deck-dev-eastus2-academy.yellowrock-2749f805.eastus2.azurecontainerapps.io/mfa-login")

        await scrape(page, test_output_path)

        await page.close()
        await browser.close()

    with open(f"{test_output_path}/data.json") as f:
        data = json.load(f)

    # validating json format
    validate(instance=data, schema=schema)

    # validating downloads
    for account in data:
        latest_bill_path = account["latest bill"]
        assert os.path.exists(latest_bill_path)
        for statement in account["statements"]:
            path = statement["download path"]
            assert os.path.exists(path)


