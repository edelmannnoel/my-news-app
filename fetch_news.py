import feedparser
import google.generativeai as genai
import json
import os
from datetime import datetime

# --- KONFIGURATION ---
# Dein API Key wird aus den GitHub Secrets geladen
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Liste der News-Quellen (RSS-Feeds)
# Du kannst hier jederzeit weitere URLs hinzufügen
RSS_SOURCES = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-sectors=business&post_type=best",
    "Reuters Markets": "https://www.reutersagency.com/feed/?best-sectors=markets&post_type=best",
    "CNBC Finance": "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance",
    "Handelsblatt": "https://www.handelsblatt.com/contentexport/feed/wirtschaft"
}

def fetch_raw_news():
    """Sammelt Schlagzeilen aus allen definierten RSS-Quellen."""
    collected_news = []
    print("Starte News-Sammlung...")
    
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            # Nimm die Top 6 Einträge pro Quelle
            for entry in feed.entries[:6]:
                # Wir speichern Titel und eine kurze Zusammenfassung (falls vorhanden)
                summary = entry.get("summary", "")[:150]
                collected_news.append(f"[{name}] {entry.title} - {summary}")
        except Exception as e:
            print(f"Fehler beim Lesen von {name}: {e}")
            
    return "\n".join(collected_news)

def generate_briefing(raw_data):
    """Verarbeitet die News mit Gemini 1.5 Flash."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    DUE BIST ein Chef-Redakteur bei einem führenden Wirtschaftsmagazin (Stil: Reuters Morning Bid / The Economist).
    
    AUFGABE: Erstelle ein exklusives morgendliches News-Briefing basierend auf den untenstehenden Rohdaten.
    
    STRUKTUR & STIL:
    1. **Titel**: Ein sehr kurzer, prägnanter Satz zum Marktsentiment heute (z.B. "Märkte atmen auf" oder "Zinsangst belastet Tech-Werte").
    2. **Headline-Sektion**: Die 3 absolut kritischsten News in einem Satz zusammengefasst.
    3. **Deep Dive**: Wähle die 2 wichtigsten Themen aus und schreibe jeweils 2-3 Sätze dazu. Analysiere kurz das "Warum".
    4. **Shorts**: 4-5 weitere wichtige Schlagzeilen als kurze Bulletpoints.
    5. **Abschluss**: Ein kurzer Satz, was Trader heute im Blick behalten sollten (z.B. Wirtschaftsdaten, Reden).

    TONALITÄT: Professionell, kühl, informativ. Keine Floskeln wie "Gern geschehen". Nutze Markdown für die Strukturierung (## für Überschriften, ** für Fettdruck).
    SPRACHE: Deutsch.

    ROHDATEN:
    {raw_data}
    """
    
    print("KI generiert das Briefing...")
    response = model.generate_content(prompt)
    return response.text

def main():
    # 1. News holen
    raw_news = fetch_raw_news()
    
    if not raw_news:
        print("Keine News gefunden. Skript wird beendet.")
        return

    # 2. KI Briefing erstellen
    briefing_content = generate_briefing(raw_news)
    
    # 3. Daten für die App strukturieren
    output_data = {
        "last_update": datetime.now().strftime("%d. %B %Y, %H:%M"),
        "content": briefing_content
    }
    
    # 4. Als JSON speichern
    with open("briefing.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("Briefing erfolgreich unter briefing.json gespeichert!")

if __name__ == "__main__":
    main()
