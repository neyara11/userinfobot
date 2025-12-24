import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ProxyConfig:
    """Управление конфигурацией SOCKS прокси для Telegram и Discord/HTTP запросов"""
    
    def __init__(self):
        """Инициализировать конфигурацию прокси из переменных окружения"""
        self.telegram_proxy_url = os.getenv('TELEGRAM_SOCKS_PROXY', '').strip()
        self.discord_proxy_url = os.getenv('DISCORD_SOCKS_PROXY', '').strip()
        
        # Логирование состояния прокси
        if self.telegram_proxy_url:
            logger.info(f"Telegram SOCKS proxy включен: {self._mask_proxy_url(self.telegram_proxy_url)}")
        else:
            logger.info("Telegram SOCKS proxy отключен")
            
        if self.discord_proxy_url:
            logger.info(f"Discord/HTTP SOCKS proxy включен: {self._mask_proxy_url(self.discord_proxy_url)}")
        else:
            logger.info("Discord/HTTP SOCKS proxy отключен")
    
    @staticmethod
    def _mask_proxy_url(proxy_url: str) -> str:
        """Скрыть учетные данные в URL прокси для логирования"""
        try:
            parsed = urlparse(proxy_url)
            if parsed.password:
                masked = proxy_url.replace(parsed.password, '***')
            else:
                masked = proxy_url
            return masked
        except:
            return "***"
    
    def get_telegram_proxy(self) -> Optional[str]:
        """Получить URL прокси для Telegram. Возвращает None если прокси отключен"""
        return self.telegram_proxy_url if self.telegram_proxy_url else None
    
    def get_discord_proxy_dict(self) -> Optional[Dict[str, str]]:
        """Получить словарь прокси для requests библиотеки (Discord/HTTP)
        
        Возвращает словарь вида:
        {
            'http': 'socks5://user:pass@host:port',
            'https': 'socks5://user:pass@host:port'
        }
        или None если прокси отключен
        """
        if not self.discord_proxy_url:
            return None
        
        return {
            'http': self.discord_proxy_url,
            'https': self.discord_proxy_url
        }
    
    def is_telegram_proxy_enabled(self) -> bool:
        """Проверить, включен ли прокси для Telegram"""
        return bool(self.telegram_proxy_url)
    
    def is_discord_proxy_enabled(self) -> bool:
        """Проверить, включен ли прокси для Discord/HTTP"""
        return bool(self.discord_proxy_url)


# Глобальный экземпляр конфигурации
proxy_config = ProxyConfig()
