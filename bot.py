import telebot
import requests
import schedule
import time
from datetime import datetime

TOKEN ="8856698929:AAHwCmuWWEIl48gxhXEfld4TqCxUNY6mcMA"
CHAT_ID = "6839097588"

bot = telebot.TeleBot(TOKEN)

# Noticias del día
def enviar_noticias():
    mensaje = """
📅 NOTICIAS IMPORTANTES DEL DÍA (UTC-3)

🔴 Revisar:
- Forex Factory
- Investing
- FXStreet

⚠️ Operar con cuidado en noticias de alto impacto.

✅ Pares:
EURUSD
GBPUSD
DXY
NAS100
SP500
US30

🕒 Revisar noticias carpeta roja / 3 estrellas.
"""
    bot.send_message(CHAT_ID, mensaje)

# Alerta antes de noticias
def alerta_noticia():
    mensaje = """
🚨 ALERTA DE NOTICIA 🚨

⛔ NO operar 5-10 minutos antes.

Esperar volatilidad y manipulación.
"""
    bot.send_message(CHAT_ID, mensaje)

# Horarios
schedule.every().day.at("07:00").do(enviar_noticias)

# Ejemplos de alertas
schedule.every().day.at("10:20").do(alerta_noticia)
schedule.every().day.at("11:20").do(alerta_noticia)

# Comando manual
@bot.message_handler(commands=['noticias'])
def noticias_manual(message):
    enviar_noticias()

print("BOT FUNCIONANDO...")

while True:
    schedule.run_pending()
    time.sleep(1)
