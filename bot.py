import telebot

TOKEN = "8856698929:AAHwCmuWWE1148gxhXEF1d4TqCXUNY6mcMA"
CHAT_ID = "6839097588"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Bot funcionando con éxito")

@bot.message_handler(commands=['noticias'])
def noticias(message):
    bot.reply_to(message, "📅 Noticias pronto")

print("Bot iniciado")

bot.infinity_polling()
