import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
import time

URL = "https://ebg-muenchen-west.de/wohnungsangebote/"
STATE_FILE = "state.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram nicht konfiguriert:")
        print(message)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


def load_state():
    if not os.path.exists(STATE_FILE):
        return set()

    with open(STATE_FILE, "r") as f:
        return set(json.load(f))


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(list(state), f)


def fetch_listings():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    listings = []

    # Heuristik: alle Links + Texte
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]

        if not text:
            continue

        # grobe Filterung (wir verfeinern das später wenn nötig)
        if "wohnung" in text.lower() or "miete" in text.lower() or "/wohnungsangebote/" in href:
            key = hashlib.sha256((text + href).encode()).hexdigest()

            listings.append({
                "key": key,
                "text": text,
                "url": href
            })

    return listings


def format_message(item):
    return f"""🏠 Neue Wohnungsanzeige

{item['text']}

🔗 {item['url']}
"""


def main():
    print("Prüfe Seite...")

    state = load_state()
    listings = fetch_listings()

    new_items = [x for x in listings if x["key"] not in state]

    if not new_items:
        print("Keine neuen Wohnungen.")
        return

    print(f"{len(new_items)} neue Einträge gefunden.")

    for item in new_items:
        send_telegram(format_message(item))
        state.add(item["key"])

    save_state(state)


if __name__ == "__main__":
    main()
