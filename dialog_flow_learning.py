import json

from environs import env
from google.cloud import dialogflow

INTENT_DISPLAY_NAME = 'Как устроиться к вам на работу'
JSON_SECTION_KEY = 'Устройство на работу'


def create_intent(
        project_id, 
        display_name, 
        training_phrases_parts, 
        message_texts
    ):
    intents_client = dialogflow.IntentsClient()

    parent = dialogflow.AgentsClient.agent_path(project_id)
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

    response = intents_client.create_intent(
        request={'parent': parent, 'intent': intent}
    )
    print('Intent created: {}'.format(response.display_name))


def main():
    env.read_env()
    project_id = env.str('DIALOG_FLOW_PROJECT_ID')

    with open('questions.json', 'r', encoding="utf-8") as my_file:
        dataset_json = my_file.read()
    dataset = json.loads(dataset_json)
    section = dataset[JSON_SECTION_KEY]
    training_phrases_parts = section['questions']
    answer = section['answer']

    create_intent(
        project_id=project_id,
        display_name=INTENT_DISPLAY_NAME,
        training_phrases_parts=training_phrases_parts,
        message_texts=[answer],
    )


if __name__ == '__main__':
    main()
