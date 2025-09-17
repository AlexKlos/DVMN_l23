import logging
import random

from environs import env
from google.cloud import dialogflow
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError, RetryError

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError, VkApiError

from telegram import Bot

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger('vk-bot')


class TelegramErrorsHandler(logging.Handler):
    def __init__(self, bot: Bot, chat_id: int):
        super().__init__(level=logging.INFO)
        self.bot = bot
        self.chat_id = chat_id
        self.setFormatter(logging.Formatter(
            fmt='[%(levelname)s] %(name)s\n%(asctime)s\n\n%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if len(msg) > 3500:
                msg = msg[:3500] + '\n...\n(truncated)'
            self.bot.send_message(chat_id=self.chat_id, text=msg)
        except Exception:
            try:
                print('Failed to send error log to Telegram chat.')
            except Exception:
                pass


def get_dialog_flow_response(project_id, session_id, text, credentials):
    try:
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(project_id, str(session_id))

        text_input = dialogflow.TextInput(text=text, language_code='Russian - ru')
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={'session': session, 'query_input': query_input}
        )
        qr = response.query_result

        logger.info(
            'Dialogflow matched intent: %s | fallback=%s | conf=%.3f | text=%r',
            getattr(qr.intent, 'display_name', '(none)'),
            getattr(qr.intent, 'is_fallback', False),
            getattr(qr, 'intent_detection_confidence', 0.0) or 0.0,
            qr.query_text,
        )

        if qr.intent.is_fallback:
            return None

        return qr.fulfillment_text or None

    except (GoogleAPICallError, RetryError) as e:
        logger.exception('Dialogflow API error: %s', e)
        return None
    except Exception as e:
        logger.exception('Unexpected Dialogflow error: %s', e)
        return None


def reply_via_dialogflow(event, vk_api_client, project_id, credentials):
    user_id = event.user_id
    user_text = (event.text or '').strip()
    if not user_text:
        logger.info('Skip empty text from user_id=%s', user_id)
        return

    message = get_dialog_flow_response(project_id, user_id, user_text, credentials)
    if not message:
        logger.info('No reply for user_id=%s (fallback or Dialogflow error)', user_id)
        return

    try:
        vk_api_client.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.randint(1, 1000)
        )
    except (ApiError, VkApiError) as e:
        logger.exception('VK API send error (user_id=%s): %s', user_id, e)
    except Exception as e:
        logger.exception('Unexpected VK send error (user_id=%s): %s', user_id, e)


def main():
    env.read_env()
    CREDENTIALS_PATH = env.str('GOOGLE_CREDENTIALS_PATH')
    DIALOG_FLOW_PROJECT_ID = env.str('DIALOG_FLOW_PROJECT_ID')
    VK_BOT_TOKEN = env.str('VK_BOT_TOKEN')

    TG_BOT_TOKEN = env.str('TG_BOT_TOKEN')
    TG_CHAT_ID = env.int('TG_CHAT_ID')

    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        logger.info('Loaded service account: %s', credentials.service_account_email)
    except Exception as e:
        logger.exception('Failed to load credentials.json: %s', e)
        return

    try:
        tg_bot = Bot(TG_BOT_TOKEN)
        error_handler = TelegramErrorsHandler(tg_bot, TG_CHAT_ID)
        logging.getLogger().addHandler(error_handler)
    except Exception as e:
        logger.exception('Failed to init Telegram error handler: %s', e)

    try:
        vk_session = vk.VkApi(token=VK_BOT_TOKEN)
        vk_api_client = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
        logger.info('VK bot started. Listening for messages...')
    except Exception as e:
        logger.exception('VK init error: %s', e)
        return

    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                reply_via_dialogflow(event, vk_api_client, DIALOG_FLOW_PROJECT_ID, credentials)
        except Exception as e:
            logger.exception('Top-level error while handling event: %s', e)


if __name__ == '__main__':
    main()
