import os
from dotenv import load_dotenv
import requests
load_dotenv()
token=os.getenv("GITHUB_TOKEN")
print(bool(token))