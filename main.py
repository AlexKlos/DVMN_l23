import logging

from environs import env
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Здравствуйте!')


# def help_command(update, context):
#     update.message.reply_text('Help!')


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    env.read_env()
    TG_BOT_TOKEN = env.str('TG_BOT_TOKEN')
    updater = Updater(TG_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    # dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()