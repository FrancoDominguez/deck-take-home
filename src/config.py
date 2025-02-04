import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv('PASSWORD')
MFACode = os.getenv('MFACODE')
username = os.getenv('USERNAME')




