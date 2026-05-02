import requests
from bs4 import BeautifulSoup

URL = "https://fentybeauty.com/en-fr/collections/makeup-face-foundation"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(URL, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")
print("Statut HTTP:", response.status_code)