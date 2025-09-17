import logging

from environs import env
from google.cloud import dialogflow
from google.oauth2 import service_account
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Здравствуйте!')


def get_dialog_flow_response(project_id, session_id, text, credentials):
    session_client = dialogflow.SessionsClient(credentials=credentials)
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code='Russian — ru')
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(
        request={'session': session, 'query_input': query_input}
    )
    qr = response.query_result
    if qr.intent.is_fallback:
        return None

    return qr.fulfillment_text


def reply_via_dialogflow(update, context):
    user_text = (update.message.text or '').strip()
    if not user_text:
        return

    project_id = context.bot_data.get('DIALOG_FLOW_PROJECT_ID')
    credentials = context.bot_data.get('GOOGLE_CREDENTIALS')
    session_id = update.effective_user.id

    answer = get_dialog_flow_response(project_id, session_id, user_text, credentials)
    if answer:
        update.message.reply_text(answer)


def main():
    env.read_env()

    TG_BOT_TOKEN = env.str('TG_BOT_TOKEN')
    DIALOG_FLOW_PROJECT_ID = env.str('DIALOG_FLOW_PROJECT_ID')
    GOOGLE_CREDENTIALS_PATH = env.str('GOOGLE_CREDENTIALS_PATH')

    credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)

    updater = Updater(TG_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['DIALOG_FLOW_PROJECT_ID'] = DIALOG_FLOW_PROJECT_ID
    dispatcher.bot_data['GOOGLE_CREDENTIALS'] = credentials

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_via_dialogflow))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
