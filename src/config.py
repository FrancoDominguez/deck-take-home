import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
MFACode = os.getenv('MFACODE')
headless_env = os.getenv('HEADLESS')

headless = True
if headless_env == "False":
    headless = False

print("printing headless var", headless)

    






