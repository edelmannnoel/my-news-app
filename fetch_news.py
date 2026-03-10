import feedparser
from google import genai
from google.genai import types # Neu für Safety Settings
import json
import os
from datetime import datetime

# --- KONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

RSS_SOURCES = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-sectors=business&post_type=best",
    "Reuters Markets": "https://www.reutersagency.com/feed/?best-sectors=markets&post_type=best",
    "CNBC Finance": "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance"
}

def fetch_raw_news():
    collected_news = []
    print("Starte News-Sammlung...")
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "Kein Titel")
                collected_news.append(f"[{name}] {title}")
        except Exception as e:
            print(f"Fehler bei {name}: {e}")
    return "\n".join(collected_news)

def generate_briefing(raw_data):
    print("KI generiert das Briefing...")
    prompt = f"Erstelle ein kurzes, professionelles News-Briefing auf Deutsch basierend auf diesen Schlagzeilen:\n{raw_data}"

    try:
        # Wir lockern die Sicherheitsfilter, damit News nicht blockiert werden
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(category="HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        if not response.text:
            return "KI gab eine leere Antwort zurück (evtl. durch Filter blockiert)."
        return response.text

    except Exception as e:
        print(f"KRITISCHER KI-FEHLER: {e}")
        return f"KI-Fehler: {str(e)}"

def main():
    raw_news = fetch_raw_news()
    if not raw_news:
        briefing_content = "Keine News-Quellen erreichbar."
    else:
        briefing_content = generate_briefing(raw_news)
    
    output_data = {
        "last_update": datetime.now().strftime("%d. %B, %H:%M Uhr"),
        "content": briefing_content
    }
    
    with open("briefing.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
