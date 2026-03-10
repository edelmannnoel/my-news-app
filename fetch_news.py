import feedparser
from google import genai
import json
import os
from datetime import datetime

# --- KONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

RSS_SOURCES = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-sectors=business&post_type=best",
    "Reuters Markets": "https://www.reutersagency.com/feed/?best-sectors=markets&post_type=best",
    "CNBC Finance": "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance",
    "Handelsblatt": "https://www.handelsblatt.com/contentexport/feed/wirtschaft"
}

def fetch_raw_news():
    collected_news = []
    print("Starte News-Sammlung...")
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                summary = entry.get("summary", "")[:150]
                collected_news.append(f"[{name}] {entry.title} - {summary}")
        except Exception as e:
            print(f"Fehler bei {name}: {e}")
    return "\n".join(collected_news)

def generate_briefing(raw_data):
    print("KI generiert das Briefing mit der neuen API...")
    
    prompt = f"""
    DUE BIST ein Chef-Redakteur bei einem führenden Wirtschaftsmagazin.
    Erstelle ein morgendliches Briefing in Deutsch basierend auf diesen Daten:
    {raw_data}
    
    STRUKTUR:
    1. Ein kurzer Titel zum Marktsentiment.
    2. Die 3 kritischsten News.
    3. Deep Dive zu 2 Themen.
    4. Kurze Bulletpoints für den Rest.
    
    Stil: Professionell, prägnant, Markdown-Format.
    """

    # Nutzung der neuen SDK Syntax
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

def main():
    raw_news = fetch_raw_news()
    if not raw_news:
        return

    briefing_content = generate_briefing(raw_news)
    
    output_data = {
        "last_update": datetime.now().strftime("%d. %B, %H:%M"),
        "content": briefing_content
    }
    
    with open("briefing.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("Erfolgreich aktualisiert!")

if __name__ == "__main__":
    main()
