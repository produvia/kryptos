import os
from flask import current_app
from telegram import Bot

from google.cloud import datastore


bot = datastore.Client.from_service_account_json('kryptos-stage-a7f9fd94cd62.json')

def send_to_user(text, user):
    if not user.telegram_id:
        current_app.logger.error(f'User {user} has no user_chat_id or telegram_id')
        raise ValueError('Can not send message to user with out chat_id')

    current_app.logger.info(f'Sending message to user {user} with telegram_id {user.telegram_id} ')
    response = bot.send_message(text=text, chat_id=user.telegram_id)
    return response
