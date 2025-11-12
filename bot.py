import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.ext import Application
import os
from typing import Dict, Any, Optional
import json
from flask import Flask, request, jsonify
import threading
import secrets

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UserInfoBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.bot = None
        self.translations = {
            'en': {
                'forwarded_user_info': 'Forwarded User Info:',
                'username': 'Username: @{username}',
                'id': 'ID: {id}',
                'first_name': 'First Name: {first_name}',
                'last_name': 'Last Name: {last_name}',
                'language_code': 'Language: {language_code}',
                'channel_info': 'Forwarded Channel Info:',
                'title': 'Title: {title}',
                'channel_username': 'Username: @{username}',
                'message_link': 'Message Link: https://t.me/{username}/{message_id}',
                'not_forwarded': 'This message was not forwarded. Showing sender info instead.',
                'no_user_info': 'No user information found in the forwarded message.'
            },
            'ru': {
                'forwarded_user_info': 'Информация о пересланном пользователе:',
                'username': 'Имя пользователя: @{username}',
                'id': 'ID: {id}',
                'first_name': 'Имя: {first_name}',
                'last_name': 'Фамилия: {last_name}',
                'language_code': 'Язык: {language_code}',
                'channel_info': 'Информация о пересланном канале:',
                'title': 'Название: {title}',
                'channel_username': 'Имя пользователя: @{username}',
                'message_link': 'Ссылка на сообщение: https://t.me/{username}/{message_id}',
                'not_forwarded': 'Это сообщение не было переслано. Показана информация об отправителе.',
                'no_user_info': 'В пересланном сообщении не найдена информация о пользователе.'
            }
        }

    def get_text(self, key: str, lang: str = 'en') -> str:
        """Get translated text based on language code"""
        if lang not in self.translations:
            lang = 'en' # fallback to English
        return self.translations[lang].get(key, key)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the /start command is issued."""
        user = update.effective_user
        lang = user.language_code if user and user.language_code else 'en'
        
        welcome_text = (
            self.get_text('forwarded_user_info', lang) + 
            "\n\n" + 
            self.get_text('not_forwarded', lang) + 
            "\n\n" + 
            "Forward a message to me and I will show you the user info."
        )
        await update.message.reply_text(welcome_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages and extract user info from forwarded messages."""
        if not update.message:
            return

        message = update.message
        lang = update.effective_user.language_code if update.effective_user and update.effective_user.language_code else 'en'
        
        # Check if the message is forwarded from a user
        if message.forward_from:
            user = message.forward_from
            response_text = self.get_text('forwarded_user_info', lang) + "\n"
            
            if user.username:
                response_text += self.get_text('username', lang).format(username=user.username) + "\n"
            
            response_text += self.get_text('id', lang).format(id=user.id) + "\n"
            response_text += self.get_text('first_name', lang).format(first_name=user.first_name) + "\n"
            
            if user.last_name:
                response_text += self.get_text('last_name', lang).format(last_name=user.last_name) + "\n"
            
            if user.language_code:
                response_text += self.get_text('language_code', lang).format(language_code=user.language_code) + "\n"
            
            await message.reply_text(response_text.strip())
        
        # Check if the message is forwarded from a channel
        elif message.forward_from_chat:
            channel = message.forward_from_chat
            response_text = self.get_text('channel_info', lang) + "\n"
            
            if channel.username:
                response_text += self.get_text('channel_username', lang).format(username=channel.username) + "\n"
            
            response_text += self.get_text('id', lang).format(id=channel.id) + "\n"
            response_text += self.get_text('title', lang).format(title=channel.title) + "\n"
            
            if message.forward_from_message_id and channel.username:
                response_text += self.get_text('message_link', lang).format(
                    username=channel.username,
                    message_id=message.forward_from_message_id
                ) + "\n"
            
            await message.reply_text(response_text.strip())
        
        # If not forwarded, show info of the sender instead
        else:
            user = message.from_user
            response_text = self.get_text('not_forwarded', lang) + "\n\n"
            
            if user.username:
                response_text += self.get_text('username', lang).format(username=user.username) + "\n"
            
            response_text += self.get_text('id', lang).format(id=user.id) + "\n"
            response_text += self.get_text('first_name', lang).format(first_name=user.first_name) + "\n"
            
            if user.last_name:
                response_text += self.get_text('last_name', lang).format(last_name=user.last_name) + "\n"
            
            if user.language_code:
                response_text += self.get_text('language_code', lang).format(language_code=user.language_code) + "\n"
            
            await message.reply_text(response_text.strip())

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a telegram message to notify the developer."""
        logger.error(msg="Exception while handling an update:", exc_info=context.error)

    async def send_message(self, chat_id: str, text: str, **kwargs):
        """Send a message to a chat ID."""
        # Create a temporary application just for sending the message
        temp_app = Application.builder().token(self.token).build()
        bot = temp_app.bot
        result = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return result
    

    def run(self, token: Optional[str] = None):
        """Run the bot with the provided token."""
        if token is not None:
            self.token = token
            
        if not self.application:
            self.application = Application.builder().token(self.token).build()
            self.bot = self.application.bot

            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)

        # Run the bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError("Please set the BOT_TOKEN environment variable")
    
    user_info_bot = UserInfoBot(bot_token)
    
if __name__ == '__main__':
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError("Please set the BOT_TOKEN environment variable")
    
    user_info_bot = UserInfoBot(bot_token)
    user_info_bot.run(bot_token)
    
    # Start the Flask app in a separate thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run the Telegram bot
    user_info_bot.run(bot_token)