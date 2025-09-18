import logging
from google.cloud import dialogflow
from google.api_core.exceptions import GoogleAPICallError, RetryError

logger = logging.getLogger('dialogflow')

def detect_intent_text(project_id, session_id, text, credentials, language_code='Russian - ru'):
    try:
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(project_id, str(session_id))

        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={'session': session, 'query_input': query_input}
        )

        qr = response.query_result
        logger.info(
            'DF intent: %s | fallback=%s | conf=%.3f | text=%r',
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
        logger.exception('Unexpected Dialogflow error: %s', e)
        return None
