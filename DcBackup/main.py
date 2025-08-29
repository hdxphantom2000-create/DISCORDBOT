#!/usr/bin/env python3
"""
Discord Translation Bot - Main Entry Point  
Simplified version based on user's bot code
"""

import discord
from googletrans import Translator
import os
from dotenv import load_dotenv
import threading
import time
from web_monitor import create_web_app, set_bot_instance

# .env laden
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("⚠️ DISCORD_TOKEN ist nicht gesetzt! Bitte .env Datei erstellen oder Secrets hinzufügen.")

# Intents setzen
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = discord.Client(intents=intents)
translator = Translator()

# Bot statistics for web monitor
bot_stats = {
    'translations': 0,
    'errors': 0,
    'status': 'Stopped'
}

# Mapping von Flagge -> Sprachcode
FLAG_LANG_MAP = {
    "🇲🇫": "fr", #französisch
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿": "en", # Englisch
    "🇩🇪": "de", "🇬🇧": "en", "🇺🇸": "en", "🇫🇷": "fr", "🇪🇸": "es",
    "🇮🇹": "it", "🇯🇵": "ja", "🇷🇺": "ru", "🇨🇳": "zh-cn", "🇰🇷": "ko",
    "🇳🇱": "nl", "🇧🇪": "nl", "🇵🇹": "pt", "🇧🇷": "pt", "🇸🇪": "sv", "🇳🇴": "no",
    "🇩🇰": "da", "🇫🇮": "fi", "🇵🇱": "pl", "🇨🇿": "cs", "🇸🇰": "sk",
    "🇭🇺": "hu", "🇬🇷": "el", "🇹🇷": "tr", "🇮🇳": "hi", "🇦🇪": "ar",
    "🇸🇦": "ar", "🇮🇱": "he", "🇹🇭": "th", "🇻🇳": "vi", "🇮🇩": "id",
    "🇲🇾": "ms", "🇺🇦": "uk", "🇧🇬": "bg", "🇷🇴": "ro", "🇭🇷": "hr",
    "🇷🇸": "sr", "🇸🇮": "sl", "🇱🇹": "lt", "🇱🇻": "lv", "🇪🇪": "et",
    "🇹🇼": "zh-tw", "🇮🇷": "fa"
}

# Übersetzung des Wortes "Übersetzung" in verschiedenen Sprachen
TRANSLATION_WORD_MAP = {
    "en": "Translation", "de": "Übersetzung", "fr": "Traduction", "es": "Traducción",
    "it": "Traduzione", "ja": "翻訳", "ru": "Перевод", "zh-cn": "翻译", "ko": "번역",
    "nl": "Vertaling", "pt": "Tradução", "sv": "Översättning", "no": "Oversettelse",
    "da": "Oversættelse", "fi": "Käännös", "pl": "Tłumaczenie", "cs": "Překlad", "sk": "Preklad",
    "hu": "Fordítás", "el": "Μετάφραση", "tr": "Çeviri", "hi": "अनुवाद", "ar": "ترجمة",
    "he": "תרגום", "th": "การแปล", "vi": "Bản dịch", "id": "Terjemahan",
    "ms": "Terjemahan", "uk": "Переклад", "bg": "Превод", "ro": "Traducere", "hr": "Prijevod",
    "sr": "Превод", "sl": "Prevod", "lt": "Vertimas", "lv": "Tulkojums", "et": "Tõlge",
    "zh-tw": "翻譯", "fa": "ترجمه"
}

# Übersetzung des Wortes "Original" in verschiedenen Sprachen
ORIGINAL_WORD_MAP = {
    "en": "Original", "de": "Original", "fr": "Original", "es": "Original",
    "it": "Originale", "ja": "元のテキスト", "ru": "Оригинал", "zh-cn": "原文", "ko": "원문",
    "nl": "Origineel", "pt": "Original", "sv": "Original", "no": "Original",
    "da": "Original", "fi": "Alkuperäinen", "pl": "Oryginalny", "cs": "Originál", "sk": "Originál",
    "hu": "Eredeti", "el": "Πρωτότυπο", "tr": "Orijinal", "hi": "मूल", "ar": "الأصل",
    "he": "מקורי", "th": "ต้นฉบับ", "vi": "Bản gốc", "id": "Asli",
    "ms": "Asal", "uk": "Оригінал", "bg": "Оригинал", "ro": "Original", "hr": "Izvornik",
    "sr": "Оригинал", "sl": "Izvirnik", "lt": "Originalas", "lv": "Oriģināls", "et": "Originaal",
    "zh-tw": "原文", "fa": "اصل"
}

# Lange Nachrichten splitten
async def send_long_message(destination, text):
    for i in range(0, len(text), 2000):
        await destination.send(text[i:i+2000])

def run_web_server():
    """Run the Flask web monitoring interface"""
    try:
        app = create_web_app()
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Fehler beim Starten des Web-Servers: {e}")

class SimpleBotWrapper:
    """Wrapper class to make the simple bot compatible with web monitor"""
    def __init__(self):
        self.stats = bot_stats
        self.FLAG_LANG_MAP = FLAG_LANG_MAP
        
    def get_stats(self):
        stats = self.stats.copy()
        if bot.is_ready():
            stats.update({
                'guilds': len(bot.guilds),
                'users': sum(guild.member_count or 0 for guild in bot.guilds),
                'latency': round(bot.latency * 1000, 2)  # in ms
            })
        return stats

# Create bot wrapper instance for web monitor
bot_wrapper = SimpleBotWrapper()

@bot.event
async def on_ready():
    bot_stats['status'] = 'Running'
    print(f"✅ Bot eingeloggt als {bot.user}")
    print(f"🔗 Bot ist in {len(bot.guilds)} Servern aktiv")
    print("🎯 Bereit für Übersetzungen!")

# Reaktion-Event für alte & neue Nachrichten
@bot.event
async def on_raw_reaction_add(payload):
    if payload.member is None or payload.member.bot:
        return

    emoji = str(payload.emoji)
    if emoji not in FLAG_LANG_MAP:
        return

    lang_code = FLAG_LANG_MAP[emoji]
    try:
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            print("⚠️ Konnte Channel nicht finden")
            return

        # Check if channel is a text channel before fetching message
        if not hasattr(channel, 'fetch_message'):
            print("⚠️ Channel unterstützt keine Nachrichten")
            return
            
        message = await channel.fetch_message(payload.message_id)
        original_text = message.content

        if not original_text.strip():
            await payload.member.send("❌ Die Nachricht enthält keinen Text zum Übersetzen.")
            return

        translated = translator.translate(original_text, dest=lang_code)
        translation_word = TRANSLATION_WORD_MAP.get(lang_code, "Übersetzung")
        original_word = ORIGINAL_WORD_MAP.get(lang_code, "Original")
        response = f"🌐 **{translation_word}** {emoji}\n**{original_word}:** {original_text}\n**{lang_code.upper()}:** {translated.text}"
        
        await send_long_message(payload.member, response)
        bot_stats['translations'] += 1
        print(f"✅ Übersetzung gesendet: {lang_code} für {payload.member}")
        
        # Reaktion entfernen nach erfolgreicher Übersetzung
        try:
            await message.remove_reaction(emoji, payload.member)
        except Exception as remove_err:
            print(f"⚠️ Konnte Reaktion nicht entfernen: {remove_err}")

    except Exception as err:
        bot_stats['errors'] += 1
        await payload.member.send(f"⚠️ Fehler beim Übersetzen: {err}")
        print(f"❌ Übersetzungsfehler: {err}")

def main():
    """Main entry point - starts both web server and Discord bot"""
    print("🚀 Starting Discord Translation Bot...")
    
    # Set bot instance for web monitor
    set_bot_instance(bot_wrapper)
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Web-Monitor gestartet auf http://0.0.0.0:5000")
    
    # Small delay to let web server start
    time.sleep(2)
    
    # Start Discord bot
    if TOKEN:
        try:
            print("🔐 Discord Token gefunden")
            print("🌐 Unterstützte Sprachen:", len(FLAG_LANG_MAP))
            bot.run(TOKEN)
        except KeyboardInterrupt:
            print("\n🛑 Bot wurde gestoppt.")
        except Exception as e:
            print(f"❌ Kritischer Fehler: {e}")
    else:
        print("❌ Kann Bot nicht starten - kein Discord Token verfügbar")
        print("🌐 Web-Monitor läuft weiter auf http://0.0.0.0:5000")
        # Keep web server running even without bot
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Anwendung gestoppt.")

if __name__ == "__main__":
    main()
