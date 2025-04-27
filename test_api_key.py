import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("DEEPSEEK_API_KEY")
print(f"DEEPSEEK_API_KEY is {'set' if api_key else 'missing'}")
if api_key:
    # Print first few characters to verify it's not empty
    print(f"Key starts with: {api_key[:5]}...")
else:
    print("No API key found. Please check your .env file.")
    print(f"Current working directory: {os.getcwd()}")
    print("Looking for .env file...")
    if os.path.exists(".env"):
        print(".env file exists!")
        with open(".env", "r") as f:
            contents = f.read()
        print(f".env file content length: {len(contents)} characters")
    else:
        print(".env file not found!") 