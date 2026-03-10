import feedparser
import google.generativeai as genai
import json
import os

# Konfiguration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# RSS Feeds (Beispiele für Reuters & Finanz-News)
FEEDS = [
    "https://www.reutersagency.com/feed/?best-sectors=business&post_type=best",
    "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance",
    "https://www.handelsblatt.com/contentexport/feed/wirtschaft"
]

def get_briefing():
    headlines = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]: # Top 5 pro Quelle
            headlines.append(f"- {entry.title}: {entry.summary[:100]}...")

    prompt = f"""
    Du bist ein Elite-Finanzjournalist. Erstelle ein morgendliches Briefing basierend auf diesen News:
    {headlines}
    
    Formatierung (Markdown):
    1. Einleitung: Ein Satz zum heutigen Marktsentiment.
    2. Die 3 wichtigsten Themen: Kurz und prägnant.
    3. 'Was heute wichtig wird': Ein Ausblick.
    
    Stil: Professionell, wie 'Guten Morgen von Reuters', aber mit modernerem Touch. Nutze Emojis dezent.
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    # Speichern als JSON für die App
    data = {"date": "Heute", "content": response.text}
    with open("briefing.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

if __name__ == "__main__":
    get_briefing()