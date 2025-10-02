"""
Webhook-compatible Telegram bot for serverless deployment
"""
import logging
import os
from telegram.ext import Application
from .telegram_bot import Telegram

logger = logging.getLogger(__name__)

class WebhookTelegram(Telegram):
    """Webhook-compatible version of Telegram bot"""
    
    def __init__(self, token, model=None, webhook_url=None):
        """Initialize webhook bot"""
        super().__init__(token, model)
        self.webhook_url = webhook_url
        
    async def setup_webhook(self):
        """Setup webhook for the bot"""
        if not self.webhook_url:
            logger.error("Webhook URL not provided")
            return False
            
        try:
            # Set webhook
            await self.application.bot.set_webhook(
                url=self.webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook set successfully: {self.webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {str(e)}")
            return False
    
    async def remove_webhook(self):
        """Remove webhook"""
        try:
            await self.application.bot.delete_webhook()
            logger.info("Webhook removed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to remove webhook: {str(e)}")
            return False
    
    def run_webhook(self, webhook_url):
        """Setup webhook mode (doesn't start polling)"""
        self.webhook_url = webhook_url
        logger.info(f"Bot configured for webhook mode: {webhook_url}")
        return self.application
