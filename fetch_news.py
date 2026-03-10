import feedparser
import ssl
from google import genai
from google.genai import types
import json
import os
from datetime import datetime

# SSL-Fix für Cloud-Umgebungen
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# --- KONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# Stabile News-Quellen
RSS_SOURCES = {
    "CNBC Finance": "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News Business": "https://news.google.com/rss/search?q=business+finance&hl=de&gl=DE&ceid=DE:de"
}

def fetch_raw_news():
    collected_news = []
    print("Starte News-Sammlung...")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    for name, url in RSS_SOURCES.items():
        try:
            print(f"Lade {name}...")
            feed = feedparser.parse(url, agent=user_agent)
            if feed.entries:
                for entry in feed.entries[:8]:
                    title = entry.get("title", "Kein Titel")
                    collected_news.append(f"[{name}] {title}")
        except Exception as e:
            print(f"Fehler bei {name}: {e}")
            
    return "\n".join(collected_news)

def generate_briefing(raw_data):
    print("KI generiert das Briefing...")
    
    prompt = f"""
    DU BIST ein Elite-Finanzjournalist. Erstelle ein deutsches News-Briefing.
    BASISDATEN:
    {raw_data}
    
    STRUKTUR:
    # TITEL
    ## TOP 3 NEWS
    ## ANALYSE (Warum ist das wichtig?)
    ## SHORTLIST (Weitere Punkte)
    """

    try:
        # KORREKTUR: Die Kategorien müssen exakt so heißen für die v1 API
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                ]
            )
        )
        
        if not response.text:
            return "KI-Antwort war leer."
        return response.text

    except Exception as e:
        print(f"Fehler bei Gemini: {e}")
        # FALLBACK: Falls die Safety Settings immer noch zicken, probieren wir es ohne
        try:
            print("Versuche Generierung ohne Safety Settings...")
            response_retry = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response_retry.text
        except:
            return f"KI-Fehler: {str(e)}"

def main():
    raw_news = fetch_raw_news()
    
    if not raw_news or len(raw_news) < 30:
        briefing_content = "Keine News gefunden. Bitte RSS-Feeds prüfen."
    else:
        briefing_content = generate_briefing(raw_news)
    
    output_data = {
        "last_update": datetime.now().strftime("%d. %B, %H:%M Uhr"),
        "content": briefing_content
    }
    
    with open("briefing.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("Fertig!")

if __name__ == "__main__":
    main()
