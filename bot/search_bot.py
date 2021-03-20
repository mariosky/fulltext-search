
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import requests
import re
import os
import json


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def search(update: Update, context: CallbackContext):
    """Query the supplied text"""
    r = None
    if context.args:
        try:
            r = requests.get('http://{}:5000/query'.format(os.getenv("SEARCH_HOST")),
                             json={'query': " ".join(context.args)},
                             auth=('user', os.getenv("API_USER_PASSWORD")),
                             timeout=3)

        except requests.exceptions.Timeout:
            update.message.reply_text('Lo siento, se me acabó el tiempo')

        if r.status_code == 200:
            results = json.loads(r.text)
            if results['documents']:
                links = " ".join(["""[{}]({}){}\n\n""".format( d['title'], d['url'][4:], d['body'])
                                  for d in results['documents']])

                update.message.reply_markdown(text=links, disable_web_page_preview=True)
                if results['total'] > 1:
                    update.message.reply_markdown(text='Encontré {} documentos en {}'.format(results['total'], results['duration']))
                else:
                    update.message.reply_markdown(text='Encontré 1 documento en {}'.format(results['duration']))

            else:
                update.message.reply_text('No encontré resultados con esas palabras')
        else:
            update.message.reply_text('Lo siento, mi servidor me contestó con este estatus'.format(r.status_code))

    else:
        update.message.reply_text('Por favor agrega algunas palabras a la búsqueda. Puedes solicitar /ayuda')






def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hola')


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_md = """Múltiples palabras, se separan con espacios: *foo* *bar* *baz*
    
    Para no incluir una palabra se usa un guión: *-palabra*
    
    Palabras exactas entre comillas: "Hola Mundo"
    
    Operador *OR*, se separan con el símbolo | : *este* | *otro*
    
    Palabras opcionales:  *palabra* *~opcional* 
    """
    update.message.reply_markdown(help_md)


def echo(update: Update, _: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ['TELEGRAM_TOKEN'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("inicio", start))
    dispatcher.add_handler(CommandHandler("ayuda", help_command))
    dispatcher.add_handler(CommandHandler("busca", search))


    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()