"""
Vercel serverless function for Telegram bot webhook
"""
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agent.agent_tools.telegram.telegram_bot import Telegram

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global bot instance
bot_instance = None

def get_bot_instance():
    """Get or create bot instance"""
    global bot_instance
    if bot_instance is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # Initialize AI model if available
        model = None
        try:
            from src.agent.agent_tools.model.model import Model
            model_api_key = os.getenv("MODEL_API_KEY")
            if model_api_key:
                model = Model(model_api_key)
                logger.info("AI model initialized for webhook")
        except Exception as e:
            logger.warning(f"Could not initialize AI model: {e}")
        
        # Create bot instance without starting polling
        bot_instance = Telegram(token=token, model=model)
        # Initialize application without running
        bot_instance._initialize_handlers_only()
        logger.info("Bot instance created for webhook")
    
    return bot_instance

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_POST(self):
        """Handle POST requests (webhook)"""
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            
            # Read request body
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            # Get bot instance
            bot = get_bot_instance()
            
            # Create Update object from webhook data
            update = Update.de_json(body, bot.application.bot)
            
            if update:
                # Process the update asynchronously
                import asyncio
                asyncio.run(bot.application.process_update(update))
                logger.info(f"Processed update: {update.update_id}")
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'Bot is running', 'method': 'webhook'}).encode())
