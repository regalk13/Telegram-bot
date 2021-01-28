from modules import telegramcalendar
from modules import weather_scraper
from modules import wiki_browser
from modules.weather_scraper import WeatherScraper
from modules.wiki_browser import WikiBrowser
import logging
from datetime import datetime, timedelta
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import requests
import json
import os
import random
from random import randint
from better_profanity import profanity
from pycoingecko import CoinGeckoAPI


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

NAME, DATE_Q, TIME_Q, INFO, OPT = range(5)
UTC_1, UTC_2 = range(2)

# ALL REMIND SYSTEM....

def json_editor(user, key, value):
    user = str(user)
    with open("data/reminder.json", "r+") as file:
        content = json.load(file)
        if user not in content["reminder"].keys():
            content["reminder"][user] = {"utc": 0, "reminder": []}
        if key == "name":
            content["reminder"][user]["reminder"].insert(0, {})
        content["reminder"][user]["reminder"][0][key] = value
        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_getter(user, ):
    with open("data/reminder.json") as file:
        content = json.load(file)
        element = content["reminder"][user]["reminder"][0]
        name = element["name"]
        date = element["date"]
        _time = element["time"]
        r_id = element["id"]
        return name, date, _time, r_id


def json_deleter(user, r_id=None, current=False):
    with open("data/reminder.json", "r+") as file:
        content = json.load(file)
        reminder = content["reminder"][user]["reminder"]
        if not current:
            for i in range(len(reminder)):
                if reminder[i]["id"] == r_id:
                    del reminder[i]
                    break
        else:
            del reminder[0]
        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_utc(user, utc=None):
    with open("data/reminder.json", "r+") as file:
        content = json.load(file)
        if utc is None:
            return content["reminder"][user]["utc"]
        else:
            content["reminder"][user]["utc"] = utc
            file.seek(0)
            json.dump(content, file)
            file.truncate()


def all_reminder(update, context):
    reply_keyboard = [["/start", "/list", "/time"]]
    username = str(update.message["chat"]["id"])
    with open("data/reminder.json") as file:
        content = json.load(file)
        reminder = content["reminder"][username]["reminder"]
        if len(reminder) == 0:
            update.message.reply_text(f"\U0001F4C3 *Lista De Reminds* \U0001F4C3\n\nNo tienes ningun remind guardado!", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True), parse_mode="markdown")
        else:
            update.message.reply_text("\U0001F4CB* Lista De Reminds *\U0001F4CB", parse_mode="markdown")
            for i, v in enumerate(reminder):
                name = v["name"]
                date = v["date"]
                _time = v["time"]
                if "opt_inf" in v.keys():
                    information = v["opt_inf"]
                    if i == len(reminder) - 1:
                        update.message.reply_text(f"{i+1}:   Nombre: {name}\n      Fecha: {date}\n      Hora: {_time}\n      Information: {information}", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
                    else:
                        update.message.reply_text(f"{i+1}:   Nombre: {name}\n      Fecha: {date}\n      Hora: {_time}\n      Information: {information}")
                else:
                    if i == len(reminder) - 1:
                        update.message.reply_text(f"{i+1}:   Nombre: {name}\n      Fecha: {date}\n      Hora: {_time}", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
                    else:
                        update.message.reply_text(f"{i+1}:   Nombre: {name}\n      Fecha: {date}\n      Hora: {_time}")


def utc_time(update, context):
    update.message.reply_text("Elige la zona horaria de tu lugar de residencia!", reply_markup=telegramcalendar.create_timezone())
    return UTC_1


def utc_time_selector(update, context):
    reply_keyboard = [["/start", "/list", "/time"]]
    selected, num = telegramcalendar.process_utc_selection(context.bot, update)
    if selected:
        chat_id = str(update.callback_query.from_user.id)
        json_utc(chat_id, utc=num)
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=f"Has elegido UTC + {num}" if num >= 0 else f"Has elegido UTC - {abs(num)}",
                        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        return ConversationHandler.END


def notification(context):
    reply_keyboard = [["/start", "/list", "/time"]]
    job = context.job
    if len(job.context) == 6:
         name, date, _time, username, r_id = job.context[1], job.context[2], job.context[3], job.context[4], job.context[5]
         context.bot.send_message(job.context[0], text=f"\U0001F4A1* Reminder *\U0001F4A1\n\nNombre: {name}\nFecha y hora {date} - {_time}.\nLlego la hora!", parse_mode="markdown")
    else:
        name, date, _time, username, r_id, information = job.context[1], job.context[2], job.context[3], job.context[4], job.context[5], job.context[6]
        context.bot.send_message(job.context[0], text=f"\U0001F4A1* Reminder *\U0001F4A1\n\nNombre: {name}\nInformación: {information}\n\nFecha y hora {date} - {_time}.\nLlego la hora!", parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    json_deleter(username, r_id=r_id)

def name(update, context):
    name = update.message.text
    if name == "/cancel":
        cancel(update, context)
        return ConversationHandler.END
    username = update.message["chat"]["id"]
    json_editor(username, "name", name)
    logger.info("Name: %s", update.message.text)
    update.message.reply_text(f"\U0001F4C5* Reminder Setup *\U0001F4C5\n\n¿Que fecha quieres para \n el remind *{name}*?",
                              reply_markup=telegramcalendar.create_calendar(), parse_mode="markdown")
    return DATE_Q

def remind(update, context):
    # print(update.message)
    update.message.reply_text("\U0001F4CD* Reminder Setup *\U0001F4CD\n\nComo se va a llamar \ntu nuevo remind?", parse_mode="markdown")
    # update.message.reply_text(f"test", reply_markup=telegramcalendar.create_clock(), parse_mode="markdown")
    return NAME


def inline_handler(update, context):
    selected, date = telegramcalendar.process_calendar_selection(context.bot, update)
    if selected:
        json_editor(str(update.callback_query.from_user.id), "date", date.strftime("%d/%m/%Y"))
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="Has elegido %s" % (date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())
        context.bot.send_message(chat_id=update.callback_query.from_user.id, text="\U0001F553* Reminder Setup *\U0001F553\n\n¿A que hora sera \n tu remind?", parse_mode="markdown", reply_markup=telegramcalendar.create_clock(user=update.callback_query.from_user.id))
        return TIME_Q


def inline_handler2(update, context):
    selected, _time = telegramcalendar.process_clock_selection(context.bot, update)
    if selected:
        chat_id = str(update.callback_query.from_user.id)
        r_id = random.randint(0, 100000)
        format_time = f"{_time[0]}:{_time[1]} {_time[2]}"
        json_editor(chat_id, "time", format_time)
        json_editor(chat_id, "id", r_id)

        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                 text=f"Has elegido {format_time}",
                                 reply_markup=ReplyKeyboardRemove())
        reply_keyboard = [["Si", "No"]]
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                text=f"\U0001F530 *Reminder Setup* \U0001F530\n\n¿Quieres añadir \nmas informacion al reminder?",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True), parse_mode="markdown")
        return INFO


def info(update, context):
    text = update.message.text
    if text == "Si":
        update.message.reply_text(f"\U00002139 *Reminder Setup* \U00002139\n\nEnvia la informacion adicional \nque quieres añadir a tu reminder!", parse_mode="markdown")
        return OPT
    else:
        reply_keyboard = [["/start", "/list", "/time"]]
        chat_id = str(update.message["chat"]["id"])
        name, date, format_time, r_id = json_getter(chat_id)
        num = json_utc(chat_id)
        hour, minute, m = int(format_time.split(" ")[0].split(":")[0]), int(format_time.split(" ")[0].split(":")[1]), format_time.split(" ")[1]

        if "pm" in m:
            n_hour = hour + 12
        else:
            n_hour = hour

        seconds = datetime.timestamp(datetime.strptime(date, "%d/%m/%Y") + timedelta(hours=n_hour, minutes=minute)) - (datetime.timestamp(datetime.now()) + (num * 3600))
        print(seconds)
        if seconds < 0:
            context.bot.send_message(chat_id=chat_id, text=f"\U0000274C*Reminder Error*\U0000274C\n\nLa fecha o hora dada esta en el pasado.\nPor favor elige una hora y fecha correctas!", parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
            json_deleter(chat_id, r_id=r_id)
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"*\U0001F4CC Saved Reminder *\U0001F4CC\n\nNombre: {name}\nFecha: {date}\nHora: {hour}:{minute} {m}",
                                     parse_mode="markdown",
                                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                      resize_keyboard=True))
            context.job_queue.run_once(notification, seconds, context=[chat_id, name, date, format_time, chat_id, r_id], name=chat_id)
        return ConversationHandler.END


def opt_info(update, context):
    reply_keyboard = [["/start", "/list", "/time"]]
    information = update.message.text
    chat_id = str(update.message["chat"]["id"])
    json_editor(chat_id, "opt_inf", information)
    name, date, format_time, r_id = json_getter(chat_id)
    num = json_utc(chat_id)
    hour, minute, m = int(format_time.split(" ")[0].split(":")[0]), int(format_time.split(" ")[0].split(":")[1]), format_time.split(" ")[1]

    if "pm" in m:
        n_hour = hour + 12
    else:
        n_hour = hour

    seconds = datetime.timestamp(datetime.strptime(date, "%d/%m/%Y") + timedelta(hours=n_hour, minutes=minute)) - (datetime.timestamp(datetime.now()) + (num * 3600))
    print(seconds)
    if seconds < 0:
        context.bot.send_message(chat_id=chat_id, text=f"\U0000274C*Reminder Error*\U0000274C\n\nLa fecha o hora dada esta en el pasado.\nPor favor elige una hora y fecha correctas!", parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        json_deleter(chat_id, r_id=r_id)
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text=f"*\U0001F4CC Saved Reminder *\U0001F4CC\n\nNombre: {name}\nFecha: {date}\nHora: {hour}:{minute} {m}",
                                 parse_mode="markdown",
                                 reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                  resize_keyboard=True))
        context.job_queue.run_once(notification, seconds, context=[chat_id, name, date, format_time, chat_id, r_id, information], name=chat_id)
    return ConversationHandler.END


def cancel(update, context):
    username = str(update.message["chat"]["id"])
    logger.info("User %s canceled the reminder setup.", username)
    json_deleter(username, current=True)
    update.message.reply_text('\U0001F53A *Reminder Setup* \U0001F53A'
                              '\n\nHas cancelado el remind!', reply_markup=ReplyKeyboardRemove(), parse_mode="markdown")
    return ConversationHandler.END

# More commands...

def start(update, context):
    logger.info(f"El usuario {update.effective_user['username']} ha iniciado una conversación")
    name = update.effective_user['first_name']
    update.message.reply_text(f"Hola {name} soy un bot multi-función creado por Juan Salazar a.k.a regalk, puedes usar /help para ver mis comandos")

def echo(update, context):
    chat_id = update.message.chat_id
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    logger.info(f"El usuario {user_id} ha enviado un msg")
    text = update.message.text
    update.message.delete()
    context.bot.sendMessage(chat_id= chat_id,parse_mode= "MarkdownV2", text=f"\n_{args}_")

def help_menu(update, context):
    chat_id = update.message.chat_id
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    name = update.effective_user['first_name']
    logger.info(f"El usuario {user_id} ha puesto el comando help!")
    context.bot.sendMessage(chat_id=chat_id, parse_mode = "Markdown", text=f"Hola 👋, {name} Estos son mis comandos: \n*💼 Comandos Basicos*\n /help - Muestra este mensaje.\n /start - Da el mensaje de inicio.\n /echo - Repito lo que digas. \n /random - Te da un número random. \n*🏅 Comandos Para Administradores*\n /add - Agrega palabras a la lista negra. \n /remove - Elimina palabras de la lista negra.\n *🕔 Comandos Remind* \n /remind - Pone un remind o alarma. \n /list - Muestra todos tus reminds pendientes.\n*💸 Crypto comandos*\n/crypto - pon el nombre de la moneda para obtener info.\n/clist - mira la lista de monedas para obtener info.")

# If user is ADMIN

def userisAdmin(chat_id, user_id, bot):
    try:
        groupadmins = bot.get_chat_administrators(chat_id)
        for admin in groupadmins:
            if admin.user.id == user_id:
                return True
        return False
    except Exception as e:
        print(e)

def add_profanity(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']
    if userisAdmin(chat_id, user_id, bot) == True:
        if len(args) == 0:
            logger.info(f"{user_id}")
            bot.sendMessage(chat_id= chat_id, text=f"{name} por favor, dame la nueva palabra...")
        else:
            with open("data/badwords.txt", "a", encoding="utf-8") as f:
                f.write("".join([f"{w}\n" for w in args]))
            logger.info(f"{user_id} new bad word..")
            bot.sendMessage(chat_id= chat_id, text=f"{name} palabra agregada a la lista negra.")
    else:
        bot.sendMessage(chat_id= chat_id, text=f"lo siento {name} no tienes permisos para esto.")

def del_profanity(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']
    if userisAdmin(chat_id, user_id, bot) == True:
        if len(args) == 0:
            logger.info(f"{user_id}")
            bot.sendMessage(chat_id= chat_id, text=f"{name} pon la palabra a retirar por favor...")
        else:
            with open("data/badwords.txt", "r", encoding="utf-8") as f:
                stored = [w.strip() for w in f.readlines()]

            with open("data/badwords.txt", "w", encoding="utf-8") as f:
                f.write("".join([f"{w}\n" for w in stored if w not in args]))

            profanity.load_censor_words_from_file("badwords.txt")
            
            logger.info(f"{user_id} palabra removida")
            bot.sendMessage(chat_id= chat_id, text=f"{name}, palabra removida.")
    else:
        bot.sendMessage(chat_id= chat_id, text=f"Lo siento {name} solo los admins pueden ejecutar este mensaje.")

def randoms(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']
    number = random.randint(1, 10)
    bot.sendMessage(chat_id=chat_id, text=f"Tú número random es: {number}")


def crypto_price(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']
    cg = CoinGeckoAPI()
    if args == ['btc']:
        data = cg.get_price(ids="bitcoin", vs_currencies='usd', include_24hr_change='true', include_last_updated_at='true')
        price = data["bitcoin"]["usd"]
        change = data["bitcoin"]['usd_24h_change']
        last_u = data["bitcoin"]['last_updated_at']

        context.bot.sendMessage(chat_id=chat_id, parse_mode="markdown", text=f"Hola {name}👋, estos son los datos de la moneda que pediste:\n*Nombre* = Bitcoin.\n*Symbol* = BTC.\n*Precio actual* = $ {price}\n*Cambio en las 24h* = {change}\n*Ultima actualización* = {last_u}")
    elif args == ['lit']:
        data = cg.get_price(ids="litecoin", vs_currencies='usd', include_24hr_change='true', include_last_updated_at='true')
        price = data["litecoin"]["usd"]
        change = data["litecoin"]['usd_24h_change']
        last_u = data["litecoin"]['last_updated_at']

        context.bot.sendMessage(chat_id=chat_id, parse_mode="markdown", text=f"Hola {name}👋, estos son los datos de la moneda que pediste:\n*Nombre* = Litecoin.\n*Symbol* = Ł.\n*Precio actual* = $ {price}\n*Cambio en las 24h* = {change}\n*Ultima actualización* = {last_u}")

    elif args == ['eth']:
        data = cg.get_price(ids="ethereum", vs_currencies='usd', include_24hr_change='true', include_last_updated_at='true')
        price = data["ethereum"]["usd"]
        change = data["ethereum"]['usd_24h_change']
        last_u = data["ethereum"]['last_updated_at']

        context.bot.sendMessage(chat_id=chat_id, parse_mode="markdown", text=f"Hola {name}👋, estos son los datos de la moneda que pediste:\n*Nombre* = Ethereum.\n*Symbol* = ETH.\n*Precio actual* = $ {price}\n*Cambio en las 24h* = {change}\n*Ultima actualización* = {last_u}")

def crypto_l(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']

    context.bot.sendMessage(chat_id=chat_id, parse_mode="markdown", text=f"Hola {name}👋, esta es la lista de monedas que tengo info:\n*btc* = Bitcoin.\n*lit* = Litecoin.\n*eth* = Ethereum.")

def get_weather(update, context):
    place_arg = ''.join(context.args)
    chat_id = update.message.chat_id
    weather = WeatherScraper(place_arg).get_tempetarure_and_weather()

    context.bot.sendMessage(chat_id= chat_id ,text=f'{weather}')

def wiki_search(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']

    if args[0] == '-': #If user wants to set a lang for example "fr-guido vann rossum"
        lang_arg = args[1].strip()
        name_arg = ''.join(context.args[2:])
        browserObj = WikiBrowser(name_arg, lang_arg)
        context.bot.sendMessage(chat_id= chat_id, text=f'{browserObj.obtain_summary()}')
    
    else: #If user doesn't want to set a lang we use the default lang(español) example "javascript"
        name_arg = ''.join(context.args)
        browserObj = WikiBrowser(name_arg)
        context.bot.sendMessage(chat_id= chat_id, text=f'{browserObj.obtain_summary()}')


def wiki_lang_list(update, context):
    bot = context.bot
    user_id = update.effective_user['id']
    args = context.args
    chat_id = update.message.chat_id
    name = update.effective_user['first_name']
    lang_list = ('-en', '-es', '-ru', '-fr', '-ar') #It's acctually a tuple but idc
    name = update.effective_user['first_name']
    nl = '\n'
    context.bot.sendMessage(chat_id= chat_id, text=f"Hola! {name}👋 esta es la lista de lenguajes permitidos:\n{nl.join(lang_list)}")


def message(update, context):
    text = update.message.text.lower()
    word = text.split()
    profanity.load_censor_words_from_file("badwords.txt")
    if profanity.contains_profanity(text) == True:
        user_id = update.effective_user['id']
        chat_id = update.message.chat_id
        name = update.effective_user['first_name']
        logger.info(f"El usuario {user_id} ha dicho una mala palabra")
        update.message.delete()
        context.bot.sendMessage(chat_id= chat_id, text=f"El mensaje de {name} fue eliminado por contener malas palabras...")
        context.bot.sendMessage(chat_id= user_id, text=f"Por favor mejora tu vocabulario o seras expulsado")
    elif word == ['hola']:
        name = update.effective_user['first_name']
        update.message.reply_text(f"Hola {name}, ¿Como estas?")



def main():
    updater = Updater("1497930060:AAFK3lLTJkP86YXSae9yv7Yhac3UgPQiksg", use_context=True)

    dp = updater.dispatcher

    all_reminder_handler = CommandHandler("list", all_reminder)
    starter = CommandHandler("start", start)
    add = CommandHandler("add", add_profanity)
    remove = CommandHandler("remove", del_profanity)
    randomer = CommandHandler("random", randoms)
    crypto = CommandHandler("crypto", crypto_price)
    crypto_list = CommandHandler("clist", crypto_l)
    weather_command = CommandHandler('weather', get_weather)
    wiki_command = CommandHandler('wiki', wiki_search)
    wiki_list = CommandHandler('wklist', wiki_lang_list)


    echo_system = CommandHandler("echo", echo)
    help_m = CommandHandler("help", help_menu)

    badwords = MessageHandler(Filters.text, message)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('remind', remind)],
        states={
            NAME: [MessageHandler(Filters.text, name)],
            DATE_Q: [CallbackQueryHandler(inline_handler)],
            TIME_Q: [CallbackQueryHandler(inline_handler2)],
            INFO: [MessageHandler(Filters.text, info)],
            OPT: [MessageHandler(Filters.text, opt_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    conv_handler_utc = ConversationHandler(
        entry_points=[CommandHandler("time", utc_time)],
        states={
            UTC_1: [CallbackQueryHandler(utc_time_selector)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(all_reminder_handler)
    dp.add_handler(starter)
    dp.add_handler(add)
    dp.add_handler(remove)
    dp.add_handler(conv_handler)
    dp.add_handler(echo_system)
    dp.add_handler(randomer)
    dp.add_handler(help_m)
    dp.add_handler(crypto)
    dp.add_handler(crypto_list)
    dp.add_handler(weather_command)
    dp.add_handler(wiki_command)
    dp.add_handler(wiki_list)
    dp.add_handler(conv_handler_utc)

    dp.add_handler(badwords)

    updater.start_polling()
    print("Bot ready")
    updater.idle()


if __name__ == '__main__':
    main()