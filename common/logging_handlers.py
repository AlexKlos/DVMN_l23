import logging

class TelegramErrorsHandler(logging.Handler):
    def __init__(self, bot, chat_id: int):
        super().__init__(level=logging.ERROR)
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
