import json

from environs import env
from google.cloud import dialogflow
from google.oauth2 import service_account

INTENT_DISPLAY_NAME = 'Вопросы от действующих партнёров'
JSON_SECTION_KEY = 'Вопросы от действующих партнёров'


def create_intent(
        project_id,
        display_name,
        training_phrases_parts,
        message_texts,
        credentials
    ):
    intents_client = dialogflow.IntentsClient(credentials=credentials)
    agents_client = dialogflow.AgentsClient(credentials=credentials)

    parent = agents_client.agent_path(project_id)

    training_phrases = []
    for phrase in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(text=phrase)
        training_phrases.append(dialogflow.Intent.TrainingPhrase(parts=[part]))

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)

    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message],
    )

    intents_client.create_intent(
        request={'parent': parent, 'intent': intent}
    )


def main():
    env.read_env()
    project_id = env.str('DIALOG_FLOW_PROJECT_ID')
    credentials_path = env.str('GOOGLE_CREDENTIALS_PATH', default='./credentials.json')
    dataset_path = env.str('DATASET_PATH', default='./questions.json')

    credentials = service_account.Credentials.from_service_account_file(credentials_path)

    with open(dataset_path, 'r', encoding='utf-8') as my_file:
        dataset = json.load(my_file)

    section = dataset[JSON_SECTION_KEY]
    training_phrases_parts = section['questions']
    answer = section['answer']

    create_intent(
        project_id=project_id,
        display_name=INTENT_DISPLAY_NAME,
        training_phrases_parts=training_phrases_parts,
        message_texts=[answer],
        credentials=credentials
    )


if __name__ == '__main__':
    main()
