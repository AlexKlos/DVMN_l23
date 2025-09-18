import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TelegramError

from common.df import detect_intent_text
from common.logging_handlers import TelegramErrorsHandler
from common.settings import load_settings

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('tg-bot')


def start(update, context):
    try:
        update.message.reply_text('Здравствуйте!')
    except TelegramError as e:
        logger.exception('Telegram send error (start): %s', e)


def reply_via_dialogflow(update, context):
    user_text = (update.message.text or '').strip()
    if not user_text:
        logger.info('Skip empty text from user_id=%s', update.effective_user.id)
        return

    cfg = context.bot_data.get('CFG')
    credentials = context.bot_data.get('CREDENTIALS')
    project_id = cfg['DIALOG_FLOW_PROJECT_ID']
    session_id = update.effective_user.id

    try:
        answer = detect_intent_text(project_id, session_id, user_text, credentials)
        if answer:
            update.message.reply_text(answer)
        else:
            logger.info('No DF reply (fallback or error) for user_id=%s', session_id)
    except TelegramError as e:
        logger.exception('Telegram send error (user_id=%s): %s', session_id, e)
    except Exception as e:
        logger.exception('Unexpected Telegram handler error: %s', e)


def main():
    try:
        cfg, credentials = load_settings()
    except Exception as e:
        logger.exception('Failed to load settings/credentials: %s', e)
        return

    try:
        updater = Updater(cfg['TG_BOT_TOKEN'], use_context=True)
        dispatcher = updater.dispatcher
        error_handler = TelegramErrorsHandler(updater.bot, cfg['TG_CHAT_ID'])
        logging.getLogger().addHandler(error_handler)
        dispatcher.bot_data['CFG'] = cfg
        dispatcher.bot_data['CREDENTIALS'] = credentials
        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_via_dialogflow))
        logger.info('Telegram bot started. Listening for messages...')
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.exception('Telegram bot init error: %s', e)


if __name__ == '__main__':
    main()
