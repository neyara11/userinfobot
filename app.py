import asyncio
import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.ext import Application
import os
from typing import Dict, Any, Optional
import json
import requests
from flask import Flask, request, jsonify
import threading
import secrets
import base64
from io import BytesIO
import time
import concurrent.futures
from proxy_config import proxy_config
try:
    from aiohttp_socks import SocksConnector
except ImportError:
    SocksConnector = None

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

APP_VERSION = "2.2.2-proxy"
logger.info(f"=============== App Version: {APP_VERSION} ===============")

class UserInfoBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.bot = None
        self.loop = None  # Event loop из telegram потока
        self._get_telegram_client_session()  # Инициализировать клиент с прокси если нужен
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
            lang = 'en'
        return self.translations[lang].get(key, key)

    def _get_telegram_client_session(self):
        """Создать ClientSession с поддержкой SOCKS прокси для Telegram"""
        if not proxy_config.is_telegram_proxy_enabled():
            return None
        
        if SocksConnector is None:
            logger.error("aiohttp-socks не установлен, но требуется для SOCKS прокси. Установите: pip install aiohttp-socks")
            return None
        
        try:
            import aiohttp
            proxy_url = proxy_config.get_telegram_proxy()
            logger.info(f"Создаю SOCKS соединитель для Telegram: {proxy_config._mask_proxy_url(proxy_url)}")
            
            connector = SocksConnector.from_url(proxy_url)
            session = aiohttp.ClientSession(connector=connector)
            return session
        except Exception as e:
            logger.error(f"Ошибка при создании SOCKS соединителя для Telegram: {e}", exc_info=True)
            return None

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
        result = await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return result

    async def send_photo(self, chat_id: str, photo: str, caption: str = None, **kwargs):
        """Отправить фото с подписью. photo может быть URL-адресом или file_id"""
        result = await self.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, **kwargs)
        return result

    async def send_media(self, chat_id: str, text: str = None, image_url: str = None, **kwargs):
        """Универсальный метод для отправки текста или фото с подписью.
        image_url может быть:
        - URL адресом (https://...)
        - base64 строкой (data:image/...;base64,...)
        - просто base64 данными
        """
        logger.info(f"Отправка сообщения в чат {chat_id}: {'через прокси' if proxy_config.is_telegram_proxy_enabled() else 'без прокси'}")
        logger.warning(f">>> send_media CALLED: chat_id={chat_id}, text={text is not None}, image_url={image_url is not None}")
        if image_url:
            logger.warning(f">>> image_url type: {type(image_url)}, length: {len(image_url) if image_url else 0}, first 100 chars: {image_url[:100] if image_url else 'NONE'}")
        
        try:
            if image_url:
                logger.warning(f">>> SENDING PHOTO! image_url={image_url[:100]}")
                
                # Проверить если это base64
                if image_url.startswith('data:image/') or not image_url.startswith('http'):
                    try:
                        logger.warning(">>> Detected base64 image, attempting to decode...")
                        # Если это data URL, извлечь base64 часть
                        if image_url.startswith('data:image/'):
                            base64_data = image_url.split(',')[1]
                        else:
                            base64_data = image_url
                        
                        # Декодировать base64 в бинарные данные
                        image_data = base64.b64decode(base64_data)
                        photo = BytesIO(image_data)
                        photo.seek(0)  # Сбросить позицию на начало
                        logger.warning(f">>> Successfully decoded base64 image, size: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f">>> Error decoding base64 image: {e}", exc_info=True)
                        photo = image_url  # Fallback to treating as URL
                else:
                    # Это URL, использовать как есть
                    photo = image_url
                    logger.warning(f">>> Detected URL image, sending to Telegram: {photo[:100]}")
                
                # Отправить фото с текстом как подписью
                logger.warning(f">>> Calling bot.send_photo with photo type={type(photo)}, caption={text}")
                result = await self.bot.send_photo(chat_id=chat_id, photo=photo, caption=text, **kwargs)
                logger.warning(f">>> Photo sent successfully, message_id: {result.message_id}")
            else:
                # Отправить просто текст
                logger.warning(f">>> SENDING TEXT MESSAGE (no image_url)")
                result = await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
                logger.warning(f">>> Message sent successfully, message_id: {result.message_id}")
        except Exception as e:
            logger.error(f">>> ERROR in send_media: {e}", exc_info=True)
            raise
        
        return result

    async def run_async(self, token: Optional[str] = None):
        """Run the bot with the provided token asynchronously."""
        if token is not None:
            self.token = token
            
        if not self.application:
            # Создать Application с поддержкой SOCKS прокси
            builder = Application.builder().token(self.token)
            
            # Если Telegram прокси включен, попытаться использовать его
            if proxy_config.is_telegram_proxy_enabled():
                try:
                    import aiohttp
                    if SocksConnector is not None:
                        proxy_url = proxy_config.get_telegram_proxy()
                        connector = SocksConnector.from_url(proxy_url)
                        session = aiohttp.ClientSession(connector=connector)
                        logger.info(f"Использую SOCKS прокси для Telegram: {proxy_config._mask_proxy_url(proxy_url)}")
                        builder = builder.get_post(session=session)
                except Exception as e:
                    logger.error(f"Ошибка при использовании SOCKS прокси для Telegram: {e}", exc_info=True)
            
            self.application = builder.build()
            self.bot = self.application.bot

            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)

        # Run the bot
        await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# Create Flask app for API endpoints
app = Flask(__name__)

# Generate a secure API token if not provided in environment
API_TOKEN = os.getenv('API_TOKEN', secrets.token_urlsafe(32))
print(f"API Token: {API_TOKEN}")  # Print the token for user to see

def require_api_token(f):
    """Decorator to require API token for authentication."""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token != f"Bearer {API_TOKEN}":
            return jsonify({'error': 'Invalid or missing API token'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Define API endpoints
@app.route('/send_message', methods=['POST'])
@require_api_token
def send_message_api():
    data = request.get_json()
    chat_id = data.get('chat_id') if data else None
    text = data.get('text') if data else None
    image_url = data.get('image_url') if data else None  # URL, file_id, или base64 строка
    
    logger.info(f"send_message_api called: chat_id={chat_id}, has_text={bool(text)}, has_image_url={bool(image_url)}")
    
    if not chat_id or (not text and not image_url):
        return jsonify({'error': 'chat_id and either text or image_url are required. image_url может быть URL, file_id или base64'}), 400
    
    # Check if it's a Discord webhook URL
    if chat_id.startswith('https://discord.com/api/webhooks/'):
        try:
            if image_url:
                # Преобразовать image_url в бинарные данные и отправить как multipart/form-data
                logger.info(f"Discord: Processing image_url for multipart upload")
                
                image_data = None
                image_filename = 'image.jpg'
                image_mimetype = 'image/jpeg'
                
                # Определить тип image_url и получить данные
                if image_url.startswith('data:image/'):
                    # Data URL с base64
                    try:
                        mime_part = image_url.split(';')[0].replace('data:', '')
                        image_mimetype = mime_part
                        if mime_part == 'image/png':
                            image_filename = 'image.png'
                        elif mime_part == 'image/gif':
                            image_filename = 'image.gif'
                        elif mime_part == 'image/webp':
                            image_filename = 'image.webp'
                        
                        base64_data = image_url.split(',')[1]
                        image_data = base64.b64decode(base64_data)
                        logger.info(f"Discord: Decoded data URL, size: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f"Discord: Error decoding data URL: {e}")
                        raise
                
                elif not image_url.startswith('http'):
                    # Обычная base64 строка
                    try:
                        image_data = base64.b64decode(image_url)
                        logger.info(f"Discord: Decoded base64 string, size: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f"Discord: Error decoding base64: {e}")
                        raise
                
                else:
                    # Это URL - скачать файл
                    try:
                        logger.info(f"Discord: Downloading image from URL: {image_url[:100]}")
                        proxies = proxy_config.get_discord_proxy_dict()
                        response = requests.get(image_url, timeout=30, proxies=proxies)
                        response.raise_for_status()
                        image_data = response.content
                        logger.info(f"Discord: Downloaded image, size: {len(image_data)} bytes")
                        
                        # Определить MIME тип из URL если возможно
                        if image_url.lower().endswith('.png'):
                            image_mimetype = 'image/png'
                            image_filename = 'image.png'
                        elif image_url.lower().endswith('.gif'):
                            image_mimetype = 'image/gif'
                            image_filename = 'image.gif'
                        elif image_url.lower().endswith('.webp'):
                            image_mimetype = 'image/webp'
                            image_filename = 'image.webp'
                    except Exception as e:
                        logger.error(f"Discord: Error downloading image from URL: {e}")
                        raise
                
                # Отправить в multipart/form-data
                files = {'file': (image_filename, BytesIO(image_data), image_mimetype)}
                data = {'content': text} if text else {}
                
                proxies = proxy_config.get_discord_proxy_dict()
                logger.info(f"Отправка в Discord: {'через прокси' if bool(proxies) else 'без прокси'}")
                logger.info(f"Discord: Sending image as multipart, filename: {image_filename}, content: {text is not None}")
                response = requests.post(chat_id, files=files, data=data, proxies=proxies)
            else:
                # Только текст
                payload = {'content': text}
                proxies = proxy_config.get_discord_proxy_dict()
                logger.info(f"Отправка в Discord: {'через прокси' if bool(proxies) else 'без прокси'}")
                logger.info(f"Discord: Sending text only")
                response = requests.post(
                    chat_id,
                    data=json.dumps(payload),
                    headers={'Content-Type': 'application/json'},
                    proxies=proxies
                )
            
            if response.status_code == 204:
                logger.info(f"Discord: Message sent successfully")
                return jsonify({'status': 'success'})
            else:
                logger.error(f"Discord: Failed with status {response.status_code}: {response.text}")
                return jsonify({'error': f'Discord webhook failed: {response.status_code} - {response.text}'}), 500
        except Exception as e:
            logger.error(f"Discord webhook error: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    # Otherwise, treat as Telegram chat ID
    try:
        logger.info(f"Preparing to send media via Telegram. image_url={image_url}")
        # Use the event loop from telegram thread via run_coroutine_threadsafe
        if user_info_bot.loop and user_info_bot.loop.is_running():
            logger.info("Using existing event loop from telegram thread")
            future = asyncio.run_coroutine_threadsafe(
                user_info_bot.send_media(chat_id, text=text, image_url=image_url),
                user_info_bot.loop
            )
            result = future.result(timeout=30)
        else:
            logger.warning("Event loop not running, using asyncio.run")
            result = asyncio.run(user_info_bot.send_media(chat_id, text=text, image_url=image_url))
        
        logger.info(f"Successfully sent message/photo with message_id: {result.message_id}")
        return jsonify({'status': 'success', 'message_id': result.message_id})
    except Exception as e:
        logger.error(f"Error in send_message_api: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/send_to_channel', methods=['POST'])
@require_api_token
def send_to_channel_api():
    data = request.get_json()
    channel_id = data.get('channel_id') if data else None
    text = data.get('text') if data else None
    image_url = data.get('image_url') if data else None  # URL, file_id, или base64 строка
    
    if not channel_id or (not text and not image_url):
        return jsonify({'error': 'channel_id and either text or image_url are required. image_url может быть URL, file_id или base64'}), 400
    
    # Check if it's a Discord webhook URL
    if channel_id.startswith('https://discord.com/api/webhooks/'):
        try:
            if image_url:
                # Преобразовать image_url в бинарные данные и отправить как multipart/form-data
                logger.info(f"Discord: Processing image_url for multipart upload")
                
                image_data = None
                image_filename = 'image.jpg'
                image_mimetype = 'image/jpeg'
                
                # Определить тип image_url и получить данные
                if image_url.startswith('data:image/'):
                    # Data URL с base64
                    try:
                        mime_part = image_url.split(';')[0].replace('data:', '')
                        image_mimetype = mime_part
                        if mime_part == 'image/png':
                            image_filename = 'image.png'
                        elif mime_part == 'image/gif':
                            image_filename = 'image.gif'
                        elif mime_part == 'image/webp':
                            image_filename = 'image.webp'
                        
                        base64_data = image_url.split(',')[1]
                        image_data = base64.b64decode(base64_data)
                        logger.info(f"Discord: Decoded data URL, size: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f"Discord: Error decoding data URL: {e}")
                        raise
                
                elif not image_url.startswith('http'):
                    # Обычная base64 строка
                    try:
                        image_data = base64.b64decode(image_url)
                        logger.info(f"Discord: Decoded base64 string, size: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f"Discord: Error decoding base64: {e}")
                        raise
                
                else:
                    # Это URL - скачать файл
                    try:
                        logger.info(f"Discord: Downloading image from URL: {image_url[:100]}")
                        proxies = proxy_config.get_discord_proxy_dict()
                        response = requests.get(image_url, timeout=30, proxies=proxies)
                        response.raise_for_status()
                        image_data = response.content
                        logger.info(f"Discord: Downloaded image, size: {len(image_data)} bytes")
                        
                        # Определить MIME тип из URL если возможно
                        if image_url.lower().endswith('.png'):
                            image_mimetype = 'image/png'
                            image_filename = 'image.png'
                        elif image_url.lower().endswith('.gif'):
                            image_mimetype = 'image/gif'
                            image_filename = 'image.gif'
                        elif image_url.lower().endswith('.webp'):
                            image_mimetype = 'image/webp'
                            image_filename = 'image.webp'
                    except Exception as e:
                        logger.error(f"Discord: Error downloading image from URL: {e}")
                        raise
                
                # Отправить в multipart/form-data
                files = {'file': (image_filename, BytesIO(image_data), image_mimetype)}
                data = {'content': text} if text else {}
                
                proxies = proxy_config.get_discord_proxy_dict()
                logger.info(f"Отправка в Discord: {'через прокси' if bool(proxies) else 'без прокси'}")
                logger.info(f"Discord: Sending image as multipart, filename: {image_filename}, content: {text is not None}")
                response = requests.post(channel_id, files=files, data=data, proxies=proxies)
            else:
                # Только текст
                payload = {'content': text}
                proxies = proxy_config.get_discord_proxy_dict()
                logger.info(f"Отправка в Discord: {'через прокси' if bool(proxies) else 'без прокси'}")
                logger.info(f"Discord: Sending text only")
                response = requests.post(
                    channel_id,
                    data=json.dumps(payload),
                    headers={'Content-Type': 'application/json'},
                    proxies=proxies
                )
            
            if response.status_code == 204:
                logger.info(f"Discord: Message sent successfully")
                return jsonify({'status': 'success'})
            else:
                logger.error(f"Discord: Failed with status {response.status_code}: {response.text}")
                return jsonify({'error': f'Discord webhook failed: {response.status_code} - {response.text}'}), 500
        except Exception as e:
            logger.error(f"Discord webhook error: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    # Otherwise, treat as Telegram channel ID
    try:
        if user_info_bot.loop and user_info_bot.loop.is_running():
            logger.info("Using existing event loop from telegram thread")
            future = asyncio.run_coroutine_threadsafe(
                user_info_bot.send_media(channel_id, text=text, image_url=image_url),
                user_info_bot.loop
            )
            result = future.result(timeout=30)
        else:
            logger.warning("Event loop not running, using asyncio.run")
            result = asyncio.run(user_info_bot.send_media(channel_id, text=text, image_url=image_url))
        
        return jsonify({'status': 'success', 'message_id': result.message_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize the bot
bot_token = os.getenv('BOT_TOKEN')
if not bot_token:
    raise ValueError("Please set the BOT_TOKEN environment variable")

user_info_bot = UserInfoBot(bot_token)

# Start the Telegram bot in a separate thread
def run_telegram_bot():
    # Create a new event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user_info_bot.loop = loop  # Save the loop reference
    
    logger.info(f"Статус подключения к Telegram: {'через прокси' if proxy_config.is_telegram_proxy_enabled() else 'без прокси'}")
    
    async def start_bot():
        if not user_info_bot.application:
            # Создать Application с поддержкой SOCKS прокси
            builder = Application.builder().token(user_info_bot.token)
            
            # Если Telegram прокси включен, попытаться использовать его
            if proxy_config.is_telegram_proxy_enabled():
                try:
                    import aiohttp
                    if SocksConnector is not None:
                        proxy_url = proxy_config.get_telegram_proxy()
                        connector = SocksConnector.from_url(proxy_url)
                        session = aiohttp.ClientSession(connector=connector)
                        logger.info(f"Используя SOCKS прокси для Telegram: {proxy_config._mask_proxy_url(proxy_url)}")
                        builder = builder.get_post(session=session)
                except Exception as e:
                    logger.error(f"Ошибка при использовании SOCKS прокси для Telegram: {e}", exc_info=True)
            
            user_info_bot.application = builder.build()
            user_info_bot.bot = user_info_bot.application.bot

            # Add handlers
            user_info_bot.application.add_handler(CommandHandler("start", user_info_bot.start))
            user_info_bot.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, user_info_bot.handle_message))
            
            # Add error handler
            user_info_bot.application.add_error_handler(user_info_bot.error_handler)

        # Use a custom run method that doesn't set signal handlers
        application = user_info_bot.application
        await application.initialize()
        await application.start()
        if application.updater:
            await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep the bot running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            if application.updater:
                await application.updater.stop()
            await application.stop()
            await application.shutdown()
    
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

telegram_thread = threading.Thread(target=run_telegram_bot)
telegram_thread.daemon = True
telegram_thread.start()
