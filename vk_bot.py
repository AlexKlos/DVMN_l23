import random

from environs import env
from google.cloud import dialogflow
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType


def get_dialog_flow_response(project_id, session_id, text):
    session_client = dialogflow.SessionsClient()
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


def reply_via_dialogflow(event, vk_api, project_id):
    user_id=event.user_id
    user_text = event.text
    message = get_dialog_flow_response(project_id, user_id, user_text)
    if message:
        vk_api.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.randint(1,1000)
        )


def main():
    env.read_env()
    DIALOG_FLOW_PROJECT_ID = env.str('DIALOG_FLOW_PROJECT_ID')
    VK_BOT_TOKEN = env.str('VK_BOT_TOKEN')
    vk_session = vk.VkApi(token=VK_BOT_TOKEN)
    
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            reply_via_dialogflow(event, vk_api, DIALOG_FLOW_PROJECT_ID)


if __name__ == '__main__':
    main()
