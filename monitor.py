
import json
import os
import requests
from bs4 import BeautifulSoup

URL = "https://ebg-muenchen-west.de/wohnungsangebote/"

STATE_FILE = "known_listings.json"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_message(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False
        },
        timeout=30
    )


def load_known():
    if not os.path.exists(STATE_FILE):
        return []

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_known(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_listings():

    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    listings = []

    # Alle Links durchsuchen
    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/properties/" in href or "/wohnungsangebote/" in href:

            title = a.get_text(" ", strip=True)

            if title:
                listings.append({
                    "title": title,
                    "url": href
                })

    # doppelte entfernen
    unique = []

    seen = set()

    for item in listings:
        if item["url"] not in seen:
            unique.append(item)
            seen.add(item["url"])

    return unique


def main():

    listings = get_listings()

    known = load_known()

    known_urls = {x["url"] for x in known}

    new = [x for x in listings if x["url"] not in known_urls]

    if new:

        for apartment in new:

            send_message(
                f"""🏠 Neue Wohnung gefunden!

{apartment['title']}

{apartment['url']}
"""
            )

        save_known(listings)

    elif not known:
        save_known(listings)
        print("Erster Lauf.")
    else:
        print("Keine neue Wohnung.")


if __name__ == "__main__":
    main()
