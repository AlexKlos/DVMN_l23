import logging
import random

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError, VkApiError
from telegram import Bot

from common.df import detect_intent_text
from common.logging_handlers import TelegramErrorsHandler
from common.logging_setup import setup_logging
from common.settings import load_settings

logger = logging.getLogger('vk-bot')


def reply_via_dialogflow(event, vk_api_client, cfg, credentials):
    session_id = event.user_id
    user_text = (event.text or '').strip()
    if not user_text:
        logger.info('Skip empty text from user_id=%s', session_id)
        return
    
    project_id = cfg['DIALOG_FLOW_PROJECT_ID']
    message = detect_intent_text(project_id, session_id, user_text, credentials)
    if not message:
        logger.info('No reply for user_id=%s (fallback or Dialogflow error)', session_id)
        return

    try:
        vk_api_client.messages.send(
            user_id=session_id,
            message=message,
            random_id=random.randint(1, 1000)
        )
    except (ApiError, VkApiError) as e:
        logger.exception('VK API send error (user_id=%s): %s', session_id, e)
    except Exception as e:
        logger.exception('Unexpected VK send error (user_id=%s): %s', session_id, e)


def main():
    global logger
    logger = setup_logging('vk-bot')

    try:
        cfg, credentials = load_settings()
    except Exception as e:
        logger.exception('Failed to load settings/credentials: %s', e)
        return

    try:
        tg_bot = Bot(cfg['TG_BOT_TOKEN'])
        error_handler = TelegramErrorsHandler(tg_bot, cfg['TG_CHAT_ID'])
        logging.getLogger().addHandler(error_handler)
    except Exception as e:
        logger.exception('Failed to init Telegram error handler: %s', e)

    try:
        vk_session = vk.VkApi(token=cfg['VK_BOT_TOKEN'])
        vk_api_client = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
        logger.info('VK bot started. Listening for messages...')
    except Exception as e:
        logger.exception('VK init error: %s', e)
        return

    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                reply_via_dialogflow(event, vk_api_client, cfg, credentials)
        except Exception as e:
            logger.exception('Top-level error while handling event: %s', e)


if __name__ == '__main__':
    main()
