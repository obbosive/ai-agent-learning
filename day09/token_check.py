import os
from dotenv import load_dotenv
load_dotenv()
token=os.getenv("GITHUB_TOKEN")
print(bool(token))