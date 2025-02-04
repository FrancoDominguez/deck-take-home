from playwright.async_api import async_playwright
from src.config import *
import os
import re
import time
import json

scraped_data = list()


# although the script is relatively short, separating it in steps made it much cleaner
# I avoided creating new files to follow the suggested project structure
async def accept_cookies(page):
    accept_cookies_button = page.locator(".cookie-buttons").locator("text='Allow all cookies'")
    # in case the button takes time to load
    await page.wait_for_timeout(1000)
    if await accept_cookies_button.is_visible():
        await accept_cookies_button.click()

async def login(page):
    username_input = page.locator("input#username")
    await username_input.wait_for(state="visible")
    await username_input.fill(username)

    password_input = page.locator("input#password")
    await password_input.wait_for(state="visible")
    await password_input.fill(password)

    continue_button = page.locator("button[type='submit']")
    await continue_button.wait_for(state="visible")
    await continue_button.click()

    await page.wait_for_load_state("networkidle")

    sms_button = page.locator("button[value='sms']")
    await sms_button.wait_for(state="visible")
    await sms_button.click()

    await page.wait_for_load_state("networkidle")

    code_input = page.locator("input#mfa_code")
    await code_input.wait_for(state="visible")
    await code_input.fill(MFACode)

    verify_button = page.locator("button[type='submit']")
    await verify_button.wait_for(state="visible")
    await verify_button.click()

async def extract_account_details(page, output_path):
    # I assume that there could be more than 2 addresses/accounts under the same login
    accounts = await page.locator(".grid.md\\:grid-cols-2.gap-6.mb-8").locator('.bg-white.rounded-lg.shadow-md.p-6').all()
    
    # for each account we will extract the main details
    for account in accounts:
        acc_details = dict()

        await account.locator("h3").nth(0).wait_for(state="visible")
        acc_name = await account.locator("h3").nth(0).text_content()
        acc_details["account name"] = acc_name

        await account.locator("p").nth(0).wait_for(state="visible")
        acc_num = await account.locator("p").nth(0).text_content()
        acc_details["account number"] = acc_num.split("#: ")[1]

        await account.locator("div", has_text="Current Balance:").nth(0).wait_for(state="visible")
        acc_details_str = await account.locator("div", has_text="Current Balance:").nth(0).text_content()
        acc_details_str = re.sub(r'\s+', ' ', acc_details_str)

        # text_content of a span extracts all values as a single string, therefore:
        acc_details["last month usage"] = acc_details_str.split("Last Month Usage: ")[-1].strip()
        acc_details["due date"] = re.search(r"Due Date:\s*(.*?)\s*Last Month Usage", acc_details_str).group(1)
        acc_details["current balance"] = re.search(r"Current Balance:\s*(.*?)\s*Due Date:", acc_details_str).group(1)

        # and download the latest bill for each account
        filename = f"{output_path}/{acc_details['account name'].replace(' ', '_')}_latest_bill.pdf"
        acc_details["latest bill"] = filename # this line saves the file path to the dict
        download_btn = account.locator("text=Latest Bill")
        await download_btn.wait_for(state="visible")

        async with page.expect_download() as download_info:
            await download_btn.click()
        download = await download_info.value
        await download.save_as(filename)
        await download_btn.click()

        acc_details["statements"] = list()
        scraped_data.append(acc_details)

async def extract_recent_statements(page, output_path):
    file_id = 0
    while True: # while loop to handle pagination with a condition at the bottom to mimic do:while
        recent_statements = page.locator("text=Recent Statements").locator("..").locator("table tbody tr")
        rows = await recent_statements.all()
        # iterating through each row
        for statement in rows:
            await statement.wait_for(state="visible")
            values = await statement.locator("td").all()

            date = (await values[1].text_content()).strip()
            amount = (await values[2].text_content()).strip()
            usage = (await values[3].text_content()).strip()
            filename = f"{output_path}/{date.replace(' ', '')}_{file_id}.pdf"
            file_id += 1

            # adding file_id is my solution to potential duplicates (they do happen)
            # putting this in a try: in case of invalid values it's important to know, perhaps logging could be added
            try:
                # associating each statement to their respective account, using a for loop to find the account
                for value in scraped_data:
                    if value["account name"] == (await values[0].text_content()).strip():
                        statement_details = {
                                "statement date": date,
                                "amount": amount,
                                "usage": usage,
                                "download path": filename
                        }

                        download_btn = statement.locator("text=Download")
                        async with page.expect_download() as download_info:
                            await download_btn.click()
                        download = await download_info.value
                        await download.save_as(filename)
                        await download_btn.click()

                        value["statements"].append(statement_details)
                        break
                else:
                    raise ValueError("invalid account name")
                time.sleep(0.2) # small delay to slow down downloads
            except Exception as e:
                print(e)

        # scroll to view the 'next' button if there is one
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)

        # checking if there is another page, if not end the loop
        next_btn = page.locator('a[href*="?page="]:has-text("Next")')
        if await next_btn.is_visible():
            await next_btn.click()
        else:
            break;
        await page.wait_for_timeout(1000)

def save_data(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "data.json")
    with open(file_path, "w") as f:
        json.dump(data, f)

# isolated this to run it in tests with headless option and to allow for potentially testing on other browsers easily
async def scrape(page, output_path):
    await accept_cookies(page)
    await login(page)
    await extract_account_details(page, output_path)
    await extract_recent_statements(page, output_path)

    save_data(scraped_data, output_path)

async def run_script():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page(java_script_enabled=True)
        # I go straight to /mfa-login login page to avoid needless playwright
        await page.goto("https://deck-dev-eastus2-academy.yellowrock-2749f805.eastus2.azurecontainerapps.io/mfa-login")
        output_path = "./output"

        await scrape(page, f"{output_path}/data.json")

        await page.close()
        await browser.close()

