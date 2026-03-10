import feedparser
import ssl
from google import genai
from google.genai import types
import json
import os
from datetime import datetime

# SSL-Zertifikatsprüfung für Cloud-Umgebungen umgehen
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# --- KONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# Wir nutzen eine Mischung aus sehr stabilen internationalen Quellen
RSS_SOURCES = {
    "CNBC Finance": "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News Business": "https://news.google.com/rss/search?q=business+finance&hl=de&gl=DE&ceid=DE:de"
}

def fetch_raw_news():
    collected_news = []
    print("Starte News-Sammlung...")
    
    # Simuliert einen echten Browser (verhindert 403 Forbidden Fehler)
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    for name, url in RSS_SOURCES.items():
        try:
            print(f"Lade {name}...")
            feed = feedparser.parse(url, agent=user_agent)
            
            if not feed.entries:
                print(f"Keine Einträge für {name}. Versuche alternative Methode...")
                continue
                
            for entry in feed.entries[:8]:
                title = entry.get("title", "Kein Titel")
                # Wir nehmen den Titel und falls vorhanden die Beschreibung
                desc = entry.get("summary", "")[:100]
                collected_news.append(f"[{name}] {title} - {desc}")
                
        except Exception as e:
            print(f"Fehler bei {name}: {e}")
            
    return "\n".join(collected_news)

def generate_briefing(raw_data):
    print("KI generiert das Briefing...")
    
    prompt = f"""
    DU BIST ein Elite-Finanzjournalist im Stil von 'Reuters Morning Bid'.
    ERSTELLE ein hochprofessionelles, deutsches News-Briefing für den heutigen Tag.
    
    QUELLDATEN:
    {raw_data}
    
    STRUKTUR (WICHTIG):
    1. # TITEL: Ein starker Satz zum Marktsentiment (z.B. DAX unter Druck, US-Tech stabil).
    2. ## TOP 3: Die drei kritischsten News-Punkte in Fettgedruckt.
    3. ## ANALYSE: Wähle das wichtigste Thema aus und erkläre in 4 Sätzen den Kontext (Warum passiert das?).
    4. ## SHORTLIST: 5-6 weitere Schlagzeilen als kompakte Liste.
    5. ---
    *Stil: Keine Begrüßung, direkt zum Punkt, kühl, analytisch.*
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(category="HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        if not response.text:
            return "KI lieferte keine Daten. Eventuell Filter-Problem."
        return response.text

    except Exception as e:
        print(f"Fehler bei Gemini: {e}")
        return f"KI-Service derzeit nicht erreichbar. (Error: {str(e)})"

def main():
    raw_news = fetch_raw_news()
    
    if not raw_news or len(raw_news) < 50:
        briefing_content = "### Derzeit keine aktuellen News-Daten verfügbar.\nBitte versuchen Sie es später erneut oder prüfen Sie die RSS-Quellen."
    else:
        briefing_content = generate_briefing(raw_news)
    
    output_data = {
        "last_update": datetime.now().strftime("%d. %B, %H:%M Uhr"),
        "content": briefing_content
    }
    
    with open("briefing.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("Update abgeschlossen!")

if __name__ == "__main__":
    main()
