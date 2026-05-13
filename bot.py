import telebot
import requests
from bs4 import BeautifulSoup
import schedule
import time
import threading
from datetime import datetime, timedelta
import pytz
import re

TOKEN = "8856698929:AAHwCmuWWE1148gxhXEF1d4TqCXUNY6mcMA"
CHAT_ID = "6839097588"

bot = telebot.TeleBot(TOKEN)

# UTC-3 (Argentina)
tz = pytz.timezone('America/Argentina/Buenos_Aires')

noticias_dia = []
noticias_publicadas = []

def obtener_noticias_investing():
    noticias = []
    try:
        url = "https://www.investing.com/economic-calendar/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        filas = soup.find_all('tr', {'class': re.compile('js-event-row')})
        for fila in filas[:40]:
            impacto = fila.find('td', {'class': 'impact'})
            if impacto and ('high' in str(impacto).lower() or '3' in str(impacto)):
                hora_elem = fila.find('td', {'class': 'time'})
                evento_elem = fila.find('td', {'class': 'event'})
                pais_elem = fila.find('td', {'class': 'flag'})
                if hora_elem and evento_elem:
                    noticias.append({
                        'hora': hora_elem.get_text(strip=True),
                        'evento': evento_elem.get_text(strip=True),
                        'pais': pais_elem.get_text(strip=True) if pais_elem else 'Global',
                        'impacto': 'ALTO',
                        'fuente': 'Investing',
                        'publicada': False
                    })
    except Exception as e:
        print(f"Error Investing: {e}")
    return noticias

def obtener_noticias_fxstreet():
    noticias = []
    try:
        url = "https://www.fxstreet.com/economic-calendar"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        eventos = soup.find_all('div', {'class': re.compile('event')})
        for evento in eventos[:40]:
            impacto = evento.find('span', {'class': re.compile('high|3')})
            if impacto:
                hora = evento.find('span', {'class': 'time'})
                nombre = evento.find('div', {'class': 'title'})
                pais = evento.find('span', {'class': 'country'})
                if hora and nombre:
                    noticias.append({
                        'hora': hora.get_text(strip=True),
                        'evento': nombre.get_text(strip=True),
                        'pais': pais.get_text(strip=True) if pais else 'Global',
                        'impacto': 'ALTO',
                        'fuente': 'FXStreet',
                        'publicada': False
                    })
    except Exception as e:
        print(f"Error FXStreet: {e}")
    return noticias

def que_se_espera(evento, pais):
    """Devuelve qué esperar según el tipo de dato económico"""
    evento_lower = evento.lower()
    pais_lower = pais.lower()
    
    # Por país y tipo de dato
    if 'fed' in evento_lower or 'fomc' in evento_lower or 'tasa' in evento_lower and 'eeuu' in pais_lower:
        return "🔹 Se espera: Definición de tasas de interés. Si suben = dólar fuerte. Si bajan = dólar débil. Impacto en SP500, NASDAQ y Oro."
    
    elif 'nfl' in evento_lower or 'nonfarm' in evento_lower or 'empleo' in evento_lower and 'eeuu' in pais_lower:
        return "🔹 Se espera: Datos de empleo EEUU. Nóminas altas = dólar sube. Bajas = dólar baja. Impacto fuerte en DXY y EURUSD."
    
    elif 'ipc' in evento_lower or 'cpi' in evento_lower or 'inflacion' in evento_lower:
        if 'eeuu' in pais_lower:
            return "🔹 Se espera: Inflación EEUU. IPC alto = más tasas = dólar fuerte. IPC bajo = dólar débil. Impacto en Oro y BTC."
        elif 'canada' in pais_lower or 'cad' in pais_lower:
            return "🔹 Se espera: Inflación Canadá. Impacto directo en USDCAD y petróleo."
        else:
            return "🔹 Se espera: Datos de inflación. Alta = moneda fuerte. Baja = moneda débil."
    
    elif 'petroleo' in evento_lower or 'oil' in evento_lower or 'crudo' in evento_lower or 'eia' in evento_lower:
        return "🔹 Se espera: Inventarios de petróleo. Bajos = petróleo sube. Altos = petróleo baja. Impacto en WTI, BRENT, CAD, MXN."
    
    elif 'eur' in evento_lower or 'euro' in evento_lower or 'bc e' in evento_lower or 'aleman' in evento_lower:
        return "🔹 Se espera: Datos de Eurozona o BCE. Impacto en EURUSD, EURGBP, DAX."
    
    elif 'libra' in evento_lower or 'gbp' in evento_lower or 'boe' in evento_lower:
        return "🔹 Se espera: Datos de Reino Unido o BoE. Impacto en GBPUSD y EURGBP."
    
    elif 'japon' in evento_lower or 'jpy' in evento_lower or 'boj' in evento_lower:
        return "🔹 Se espera: Datos de Japón o BoJ. Impacto en USDJPY."
    
    elif 'canada' in evento_lower or 'cad' in evento_lower:
        return "🔹 Se espera: Datos de Canadá. Impacto en USDCAD, relacionado con petróleo."
    
    elif 'australia' in evento_lower or 'aud' in evento_lower:
        return "🔹 Se espera: Datos de Australia. Impacto en AUDUSD."
    
    elif 'china' in evento_lower or 'yuan' in evento_lower:
        return "🔹 Se espera: Datos de China. Impacto en AUD, NZD, materias primas."
    
    else:
        return f"🔹 Se espera: Publicación de dato económico de {pais}. Impacto moderado en pares relacionados."

def obtener_todas_noticias():
    print("Buscando noticias de alto impacto...")
    investing = obtener_noticias_investing()
    fxstreet = obtener_noticias_fxstreet()
    
    todas = investing + fxstreet
    vistas = set()
    unicas = []
    for n in todas:
        clave = f"{n['hora']}_{n['evento']}_{n['pais']}"
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(n)
    
    unicas.sort(key=lambda x: x['hora'])
    return unicas

def generar_mensaje_noticias():
    global noticias_dia
    noticias_dia = obtener_todas_noticias()
    
    ahora = datetime.now(tz)
    hora_actual = ahora.strftime("%H:%M")
    
    mensaje = f"📅 **CALENDARIO ALTO IMPACTO - UTC-3**\n🇦🇷 Hora Argentina: {hora_actual}\n\n"
    
    ya_salieron = []
    faltan = []
    
    for n in noticias_dia:
        try:
            hora_n = datetime.strptime(n['hora'], "%H:%M").replace(year=ahora.year, month=ahora.month, day=ahora.day)
            hora_n = tz.localize(hora_n)
            if hora_n < ahora:
                ya_salieron.append(n)
            else:
                faltan.append(n)
        except:
            faltan.append(n)
    
    if ya_salieron:
        mensaje += "✅ **YA SALIERON:**\n"
        for n in ya_salieron:
            mensaje += f"• {n['hora']} - {n['evento']} ({n['pais']})\n"
        mensaje += "\n"
    
    if faltan:
        mensaje += "⏳ **PRÓXIMAS NOTICIAS:**\n"
        for n in faltan[:15]:
            mensaje += f"• {n['hora']} - {n['evento']} ({n['pais']})\n"
        mensaje += "\n"
    
    if not ya_salieron and not faltan:
        mensaje += "⚠️ No hay noticias de alto impacto programadas.\n\n"
    
    mensaje += "⏰ Alerta 10 min antes | 📊 Análisis 1 min después"
    return mensaje

def enviar_analisis(noticia):
    """Envía análisis 1 minuto después de la noticia"""
    analisis = que_se_espera(noticia['evento'], noticia['pais'])
    
    mensaje = f"📊 **ANÁLISIS POST-NOTICIA**\n\n"
    mensaje += f"📢 {noticia['evento']}\n"
    mensaje += f"🕒 {noticia['hora']} hs | 🌍 {noticia['pais']}\n\n"
    mensaje += f"{analisis}\n\n"
    mensaje += "⚠️ Esperar 5-10 minutos para confirmar dirección."
    
    bot.send_message(CHAT_ID, mensaje)

def programar_todo():
    global noticias_dia, noticias_publicadas
    
    ahora = datetime.now(tz)
    noticias_publicadas = []
    
    # Limpiar jobs viejos
    schedule.clear()
    
    # Reprogramar resumen diario
    schedule.every().day.at("06:00").do(enviar_resumen_manana)
    
    for n in noticias_dia:
        try:
            hora_n = datetime.strptime(n['hora'], "%H:%M").replace(year=ahora.year, month=ahora.month, day=ahora.day)
            hora_n = tz.localize(hora_n)
            
            if hora_n > ahora:
                # Alerta 10 minutos antes
                hora_alerta = hora_n - timedelta(minutes=10)
                if hora_alerta > ahora:
                    def crear_alerta(noticia=n):
                        def alerta():
                            msg = f"🚨 **ALERTA** 🚨\n\n📢 {noticia['evento']}\n🕒 Sale en 10 minutos: {noticia['hora']}\n🌍 {noticia['pais']}\n\n⛔ **NO OPERAR** hasta 10 minutos después de la noticia."
                            bot.send_message(CHAT_ID, msg)
                        return alerta
                    schedule.every().day.at(hora_alerta.strftime("%H:%M")).do(crear_alerta())
                
                # Análisis 1 minuto después
                hora_post = hora_n + timedelta(minutes=1)
                def crear_post(noticia=n):
                    def post():
                        if not noticia.get('publicada', False):
                            noticia['publicada'] = True
                            noticias_publicadas.append(noticia)
                            enviar_analisis(noticia)
                    return post
                schedule.every().day.at(hora_post.strftime("%H:%M")).do(crear_post())
                
        except Exception as e:
            print(f"Error con noticia {n.get('hora')}: {e}")

def enviar_resumen_manana():
    mensaje = generar_mensaje_noticias()
    bot.send_message(CHAT_ID, mensaje)
    programar_todo()
    print("Notificaciones programadas - UTC-3")

# Comandos
@bot.message_handler(commands=['start', 'ayuda'])
def ayuda(message):
    bot.reply_to(message, "🤖 **BOT NOTICIAS ALTO IMPACTO - UTC-3**\n\n/noticias - Calendario del día\n/proxima - Próxima noticia\n/ultimas - Últimas publicadas\n/ayuda - Comandos\n\n📊 10 min antes: ALERTA\n📊 1 min después: ANÁLISIS")

@bot.message_handler(commands=['noticias'])
def noticias_cmd(message):
    bot.reply_to(message, generar_mensaje_noticias())
    programar_todo()

@bot.message_handler(commands=['ultimas'])
def ultimas_cmd(message):
    if noticias_publicadas:
        mensaje = "📰 **ÚLTIMAS NOTICIAS PUBLICADAS:**\n\n"
        for n in noticias_publicadas[-5:]:
            mensaje += f"• {n['hora']} - {n['evento']} ({n['pais']})\n"
        bot.reply_to(message, mensaje)
    else:
        bot.reply_to(message, "Todavía no salió ninguna noticia hoy.")

@bot.message_handler(commands=['proxima'])
def proxima_cmd(message):
    ahora = datetime.now(tz)
    for n in noticias_dia:
        try:
            hora_n = datetime.strptime(n['hora'], "%H:%M").replace(year=ahora.year, month=ahora.month, day=ahora.day)
            hora_n = tz.localize(hora_n)
            if hora_n > ahora and not n.get('publicada', False):
                bot.reply_to(message, f"⏰ **PRÓXIMA NOTICIA:**\n\n{n['hora']} - {n['evento']}\n🌍 {n['pais']}\n\n🔔 Alerta 10 min antes\n📊 Análisis 1 min después")
                return
        except:
            pass
    bot.reply_to(message, "No hay más noticias de alto impacto hoy.")

@bot.message_handler(func=lambda message: True)
def preguntas(message):
    texto = message.text.lower()
    
    if "dolar" in texto or "dxy" in texto:
        bot.reply_to(message, "💵 **DXY:** Esperar datos de empleo, inflación o FED. Esos mueven el dólar fuerte.")
    elif "eurusd" in texto or "euro" in texto:
        bot.reply_to(message, "🇪🇺 **EURUSD:** Atento a noticias de BCE, Alemania o inflación de EEUU.")
    elif "libra" in texto or "gbp" in texto:
        bot.reply_to(message, "🇬🇧 **GBPUSD:** Sensible a noticias de BoE y Reino Unido.")
    elif "canada" in texto or "cad" in texto or "usdcad" in texto:
        bot.reply_to(message, "🇨🇦 **USDCAD:** Mirar noticias de petróleo, inflación de Canadá y empleo.")
    elif "japon" in texto or "jpy" in texto:
        bot.reply_to(message, "🇯🇵 **USDJPY:** Atento a noticias de BoJ y tasas de EEUU.")
    elif "oro" in texto or "gold" in texto:
        bot.reply_to(message, "🥇 **Oro:** Sensible a inflación de EEUU y decisiones de FED.")
    elif "petroleo" in texto or "wti" in texto:
        bot.reply_to(message, "🛢️ **Petróleo:** Mirar inventarios EIA y noticias de OPEP.")
    else:
        bot.reply_to(message, "Usá /noticias para ver el calendario. Preguntame por: dolar, eurusd, libra, canada, japon, oro, petroleo")

# Iniciar
print("🚀 BOT INICIADO - UTC-3 | Alto impacto | Alertas y análisis")
threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()

while True:
    schedule.run_pending()
    time.sleep(5)
