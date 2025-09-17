import logging

from environs import env
from google.cloud import dialogflow
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError, RetryError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TelegramError

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


def get_dialog_flow_response(project_id, session_id, text, credentials):
    try:
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(project_id, str(session_id))

        text_input = dialogflow.TextInput(text=text, language_code='Russian — ru')
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={'session': session, 'query_input': query_input}
        )

        qr = response.query_result
        logger.info(
            'DF matched intent: %s | fallback=%s | conf=%.3f | text=%r',
            getattr(qr.intent, 'display_name', '(none)'),
            getattr(qr.intent, 'is_fallback', False),
            getattr(qr, 'intent_detection_confidence', 0.0) or 0.0,
            qr.query_text
        )

        if qr.intent.is_fallback:
            return None

        return qr.fulfillment_text or None

    except (GoogleAPICallError, RetryError) as e:
        logger.exception('Dialogflow API error: %s', e)
        return None
    except Exception as e:
        logger.exception('Unexpected DF error: %s', e)
        return None


def reply_via_dialogflow(update, context):
    user_text = (update.message.text or '').strip()
    if not user_text:
        logger.info('Skip empty text from user_id=%s', update.effective_user.id)
        return

    project_id = context.bot_data.get('DIALOG_FLOW_PROJECT_ID')
    credentials = context.bot_data.get('GOOGLE_CREDENTIALS')
    session_id = update.effective_user.id

    try:
        answer = get_dialog_flow_response(project_id, session_id, user_text, credentials)
        if answer:
            update.message.reply_text(answer)
        else:
            logger.info('No DF reply (fallback or error) for user_id=%s', session_id)
    except TelegramError as e:
        logger.exception('Telegram send error (user_id=%s): %s', session_id, e)
    except Exception as e:
        logger.exception('Unexpected Telegram handler error: %s', e)


def main():
    env.read_env()

    TG_BOT_TOKEN = env.str('TG_BOT_TOKEN')
    DIALOG_FLOW_PROJECT_ID = env.str('DIALOG_FLOW_PROJECT_ID')
    GOOGLE_CREDENTIALS_PATH = env.str('GOOGLE_CREDENTIALS_PATH')

    try:
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
        logger.info('Loaded service account: %s', credentials.service_account_email)
    except Exception as e:
        logger.exception('Failed to load credentials.json: %s', e)
        return

    try:
        updater = Updater(TG_BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.bot_data['DIALOG_FLOW_PROJECT_ID'] = DIALOG_FLOW_PROJECT_ID
        dispatcher.bot_data['GOOGLE_CREDENTIALS'] = credentials

        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_via_dialogflow))

        logger.info('Telegram bot started. Listening for messages...')
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.exception('Telegram bot init error: %s', e)


if __name__ == '__main__':
    main()
