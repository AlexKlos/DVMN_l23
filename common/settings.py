import logging
from environs import env
from google.oauth2 import service_account

logger = logging.getLogger('settings')

def load_settings():
    env.read_env()
    cfg = {
        'TG_BOT_TOKEN': env.str('TG_BOT_TOKEN'),
        'VK_BOT_TOKEN': env.str('VK_BOT_TOKEN', default=None),
        'TG_CHAT_ID': env.int('TG_CHAT_ID'),
        'DIALOG_FLOW_PROJECT_ID': env.str('DIALOG_FLOW_PROJECT_ID'),
        'GOOGLE_CREDENTIALS_PATH': env.str('GOOGLE_CREDENTIALS_PATH'),
    }
    credentials = service_account.Credentials.from_service_account_file(cfg['GOOGLE_CREDENTIALS_PATH'])
    logger.info('Loaded service account: %s', credentials.service_account_email)
    return cfg, credentials
