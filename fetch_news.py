import feedparser
from google import genai
import json
import os
from datetime import datetime

# --- KONFIGURATION ---
# Wir nutzen die stabile API v1, um den 404-Fehler zu vermeiden
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# Deine News-Quellen
RSS_SOURCES = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-sectors=business&post_type=best",
    "Reuters Markets": "https://www.reutersagency.com/feed/?best-sectors=markets&post_type=best",
    "CNBC Finance": "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance",
    "Handelsblatt": "https://www.handelsblatt.com/contentexport/feed/wirtschaft"
}

def fetch_raw_news():
    """Sammelt Schlagzeilen aus den RSS-Feeds."""
    collected_news = []
    print("Starte News-Sammlung...")
    
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"Warnung: Keine Einträge in {name} gefunden.")
                continue
                
            # Top 6 Einträge pro Quelle sammeln
            for entry in feed.entries[:6]:
                title = entry.get("title", "Kein Titel")
                summary = entry.get("summary", "")[:150]
                collected_news.append(f"[{name}] {title} - {summary}")
        except Exception as e:
            print(f"Fehler beim Abrufen von {name}: {e}")
            
    return "\n".join(collected_news)

def generate_briefing(raw_data):
    """Verarbeitet die News mit Gemini 1.5 Flash (v1 Stable)."""
    print("KI generiert das Briefing...")
    
    prompt = f"""
    DU BIST ein Elite-Finanzjournalist. Erstelle ein exklusives morgendliches Briefing in Deutsch.
    
    BASISDATEN:
    {raw_data}
    
    STRUKTUR (Markdown):
    1. # Ein prägnanter Titel zum heutigen Marktsentiment.
    2. ## Die 3 wichtigsten Ereignisse (kurz zusammengefasst).
    3. ## Hintergrund & Analyse: Wähle die 2 spannendsten Themen und erkläre sie in 3-4 Sätzen.
    4. ## Weitere Schlagzeilen: 5 Bulletpoints für den schnellen Überblick.
    5. ---
    *Fokus: Professionell, wie Reuters Morning Bid, keine unnötigen Floskeln.*
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Fehler bei der KI-Generierung: {e}")
        return "Fehler: Das Briefing konnte nicht generiert werden."

def main():
    # 1. Daten sammeln
    raw_news = fetch_raw_news()
    
    if not raw_news:
        print("Kritischer Fehler: Keine News-Daten verfügbar.")
        return

    # 2. KI-Zusammenfassung erstellen
    briefing_content = generate_briefing(raw_news)
    
    # 3. JSON für die App vorbereiten
    # Wir nutzen ein schönes Datumsformat für den "Stand"-Text in der App
    now = datetime.now()
    formatted_date = now.strftime("%d. %B, %H:%M Uhr")
    
    output_data = {
        "last_update": formatted_date,
        "content": briefing_content
    }
    
    # 4. Datei speichern (wird von GitHub Action committet)
    try:
        with open("briefing.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"Erfolg! Briefing wurde um {formatted_date} aktualisiert.")
    except Exception as e:
        print(f"Fehler beim Speichern der Datei: {e}")

if __name__ == "__main__":
    main()
