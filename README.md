import telebot

TOKEN = "8856698929:AAHwCmuWWE1148gxhXEF1d4TqCXUNY6mcMA"
CHAT_ID = "6839097588"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Bot funcionando correctamente")

@bot.message_handler(commands=['noticias'])
def noticias(message):
    bot.reply_to(message, "📅 Próximamente: noticias de alto impacto")

print("Bot iniciado correctamente")

bot.infinity_polling()
