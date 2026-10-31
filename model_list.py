import os, requests
from dotenv import load_dotenv

load_dotenv()
r = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": "Bearer " + os.getenv("GROQ_API_KEY")},
)
print([m["id"] for m in r.json()["data"]])