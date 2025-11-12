# Userinfobot

A Telegram bot that displays user info when a message is forwarded to it. Mainly used for finding the user ID.

## Описание

Telegram-бот, который отображает информацию о пользователе, когда сообщение пересылается в него. В основном используется для поиска ID пользователя.

## Features

- Shows user information when a message is forwarded to the bot
- Supports both forwarded user messages and channel posts
- Multilingual support (English and Russian)
- Asynchronous implementation for better performance
- Docker support for easy deployment

## Возможности

- Показывает информацию о пользователе, когда сообщение пересылается боту
- Поддерживает как пересланные сообщения от пользователей, так и посты из каналов
- Многоязычная поддержка (английский и русский)
- Асинхронная реализация для лучшей производительности
- Поддержка Docker для легкого развертывания

## Requirements

- Python 3.8+
- Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))

## Требования

- Python 3.8+
- Токен Telegram-бота (получите у [@BotFather](https://t.me/BotFather))

## Local Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd userinfobot
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the `.env.example`:
```bash
cp .env.example .env
```

4. Add your bot token to the `.env` file:
```bash
BOT_TOKEN=your_bot_token_here
```

5. Run the bot:
```bash
python bot.py
```

## Локальная установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd userinfobot
```

2. Установите необходимые зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Добавьте токен бота в файл `.env`:
```bash
BOT_TOKEN=your_bot_token_here
```

5. Запустите бота:
```bash
python bot.py
```

## Docker Installation

1. Build and run the bot with Docker Compose:
```bash
docker-compose up -d
```

## System Service Installation (Ubuntu)

To install the bot as a system service on Ubuntu, follow these steps:

1. Install Docker and Docker Compose if not already installed:
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

2. Copy the `run_bot.sh` file to `/opt/userinfobot/` (or your preferred directory) and make it executable:
```bash
sudo chmod +x /opt/userinfobot/run_bot.sh
```

3. Run the service installation (as root or with sudo):
```bash
sudo /opt/userinfobot/run_bot.sh install
```

4. After installation, you can use the following commands:
```bash
sudo systemctl start userinfobot    # Start the service
sudo systemctl stop userinfobot     # Stop the service
sudo systemctl restart userinfobot  # Restart the service
sudo systemctl status userinfobot   # Check service status
```

5. To enable auto-start on system boot:
```bash
sudo systemctl enable userinfobot
```

## Установка с Docker

1. Соберите и запустите бота с помощью Docker Compose:
```bash
docker-compose up -d
```

## Установка как системный сервис (Ubuntu)

Для установки бота как системного сервиса на Ubuntu выполните следующие шаги:

1. Установите Docker и Docker Compose, если они еще не установлены:
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

2. Скопируйте файл `run_bot.sh` в `/opt/userinfobot/` (или в нужную директорию) и сделайте его исполняемым:
```bash
sudo chmod +x /opt/userinfobot/run_bot.sh
```

3. Запустите установку сервиса (из под root или с sudo):
```bash
sudo /opt/userinfobot/run_bot.sh install
```

4. После установки сервиса можно использовать следующие команды:
```bash
sudo systemctl start userinfobot    # Запуск сервиса
sudo systemctl stop userinfobot     # Остановка сервиса
sudo systemctl restart userinfobot  # Перезапуск сервиса
sudo systemctl status userinfobot   # Проверка статуса сервиса
```

5. Для автоматического запуска сервиса при старте системы:
```bash
sudo systemctl enable userinfobot
```

## Configuration

The bot uses environment variables for configuration:

- `BOT_TOKEN`: Your Telegram bot token (required)
- `API_TOKEN`: Your API token for authentication (optional, auto-generated if not provided)

## Конфигурация

Бот использует переменные окружения для настройки:

- `BOT_TOKEN`: Токен вашего Telegram-бота (обязательно)
- `API_TOKEN`: Токен для аутентификации API (опционально, генерируется автоматически если не задан)

## Usage

1. Forward any message to the bot
2. The bot will display information about the original sender or channel
3. For forwarded messages from users, the bot shows:
   - Username
   - User ID
   - First and last name
   - Language code
4. For forwarded messages from channels, the bot shows:
   - Channel username
   - Channel ID
   - Channel title
   - Link to the original message (if available)

## API Usage

The bot also provides API endpoints for external control with authentication required:

### Send a message to a user
Send a POST request to `/send_message` with JSON payload and authentication header:
```bash
curl -X POST http://localhost:5000/send_message \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "user_chat_id",
    "text": "Your message text"
  }'
```

### Send a message to a channel
Send a POST request to `/send_to_channel` with JSON payload and authentication header:
```bash
curl -X POST http://localhost:5000/send_to_channel \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "channel_id",
    "text": "Your message text"
  }'
```

## Использование

1. Перешлите любое сообщение боту
2. Бот отобразит информацию об изначальном отправителе или канале
3. Для пересланных сообщений от пользователей бот показывает:
   - Имя пользователя
   - ID пользователя
   - Имя и фамилию
   - Код языка
4. Для пересланных сообщений из каналов бот показывает:
   - Имя пользователя канала
   - ID канала
   - Название канала
   - Ссылку на исходное сообщение (если доступно)

## Использование API

Бот также предоставляет API-эндпоинты для внешнего управления с обязательной аутентификацией:

### Отправить сообщение пользователю
Отправьте POST-запрос на `/send_message` с JSON-данными и заголовком аутентификации:
```bash
curl -X POST http://localhost:5000/send_message \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "id_чата_пользователя",
    "text": "Текст вашего сообщения"
  }'
```

### Отправить сообщение в канал
Отправьте POST-запрос на `/send_to_channel` с JSON-данными и заголовком аутентификации:
```bash
curl -X POST http://localhost:5000/send_to_channel \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "id_канала",
    "text": "Текст вашего сообщения"
  }'
```

## Безопасность

Для доступа к API-эндпоинтам требуется токен аутентификации в формате Bearer.
Токен генерируется автоматически при запуске бота, или может быть задан в переменной окружения `API_TOKEN`.

## Security

Access to API endpoints requires an authentication token in Bearer format.
The token is auto-generated when the bot starts, or can be set via the `API_TOKEN` environment variable.

## Production Deployment

For production deployment, the bot uses Gunicorn as a WSGI HTTP server to handle API requests, which provides better performance and stability compared to the development server. The Docker container is configured to run the bot with Gunicorn automatically.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.