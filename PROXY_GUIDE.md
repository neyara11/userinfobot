# Руководство по использованию SOCKS прокси

Этот проект поддерживает работу через SOCKS прокси для Telegram и Discord/HTTP запросов отдельно.

## Установка зависимостей

Для работы с SOCKS прокси необходимо установить дополнительные пакеты:

```bash
pip install -r requirements.txt
```

Убедитесь, что в `requirements.txt` присутствуют:
- `PySocks>=1.7.1` - основная библиотека для SOCKS протокола
- `aiohttp-socks>=0.8.4` - поддержка SOCKS в aiohttp (для Telegram бота)

## Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example` и настройте переменные:

```bash
# скопировать шаблон
cp .env.example .env
```

#### Telegram SOCKS Proxy

Переменная: `TELEGRAM_SOCKS_PROXY`

Примеры формата:

- **SOCKS5 с аутентификацией**:
  ```
  TELEGRAM_SOCKS_PROXY=socks5://username:password@proxy.example.com:1080
  ```

- **SOCKS5 без аутентификации**:
  ```
  TELEGRAM_SOCKS_PROXY=socks5://proxy.example.com:1080
  ```

- **SOCKS4**:
  ```
  TELEGRAM_SOCKS_PROXY=socks4://proxy.example.com:1080
  ```

- **Отключить прокси** (по умолчанию):
  ```
  TELEGRAM_SOCKS_PROXY=
  ```

#### Discord/HTTP SOCKS Proxy

Переменная: `DISCORD_SOCKS_PROXY`

Используется для отправки сообщений в Discord и загрузки изображений по URL.

Примеры формата - те же самые, что для Telegram:

```
DISCORD_SOCKS_PROXY=socks5://username:password@proxy.example.com:1080
```

## Пример .env файла

```env
BOT_TOKEN=your_bot_token_here
API_TOKEN=your_api_token_here

# Telegram SOCKS Proxy (отключен)
TELEGRAM_SOCKS_PROXY=

# Discord/HTTP SOCKS Proxy с аутентификацией
DISCORD_SOCKS_PROXY=socks5://user:pass@proxy.example.com:1080
```

## Логирование

При запуске приложение выведет информацию о состоянии прокси:

```
INFO:proxy_config:Telegram SOCKS proxy отключен
INFO:proxy_config:Discord/HTTP SOCKS proxy включен: socks5://user:***@proxy.example.com:1080
INFO:app:Используя SOCKS прокси для Telegram: socks5://***@proxy.example.com:1080
```

Пароли скрываются в логах для безопасности.

## Независимая конфигурация

Важное преимущество этой реализации:

- **Telegram прокси** работает независимо от Discord прокси
- Можно включить только один из них
- Можно использовать разные прокси для разных сервисов
- Если прокси отключен, приложение работает без него

## Возможные проблемы

### "aiohttp-socks не установлен"

**Решение**: Установите пакет:
```bash
pip install aiohttp-socks>=0.8.4
```

### Ошибка подключения к прокси

Проверьте:
1. Правильность формата URL прокси
2. Доступность сервера прокси
3. Правильность учетных данных (если требуются)
4. Разрешение портов в брандмауэре

## Тестирование

Для проверки работы прокси можно использовать логи. При успешном подключении через прокси вы увидите сообщения типа:

```
INFO:app:Используя SOCKS прокси для Telegram: socks5://***@proxy.example.com:1080
```

В случае ошибок будут выведены соответствующие сообщения об ошибках:

```
ERROR:app:Ошибка при использовании SOCKS прокси для Telegram: ...
```

## Техническая информация

### Как работает Telegram прокси

1. Используется `aiohttp-socks` для создания `SocksConnector`
2. Коннектор передается в `ClientSession`
3. Session используется в Telegram Application для всех запросов к API Telegram

### Как работает Discord/HTTP прокси

1. Используется `requests` библиотека с параметром `proxies`
2. Прокси применяется к запросам загрузки изображений и отправке в Discord
3. Формат: словарь с ключами 'http' и 'https'

## Безопасность

- Пароли в URL прокси скрывают в логах
- Переменные окружения не хранятся в git
- Используйте `.env` файл, который не коммитится в репозиторий
