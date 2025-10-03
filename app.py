import os
import json
import logging
from flask import Flask, request, jsonify
from src.agent.agent_tools.telegram.telegram_webhook import TelegramWebhook

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

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
        
        # Create bot instance
        bot_instance = TelegramWebhook(token=token, model=model)
        # Initialize application without running
        bot_instance._initialize_handlers_only()
        logger.info("Bot instance created for webhook")
    
    return bot_instance

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "Bot is running and ready for Telegram webhooks!",
        "message": "Visit /webhook to receive Telegram updates.",
        "commands": [
            "/price <symbol>",
            "/trending", 
            "/funds",
            "/drophunting"
        ],
        "natural_language_examples": [
            "What's the price of Bitcoin?",
            "Show me trending cryptocurrencies",
            "Top crypto investors and funds",
            "Show me airdrop activities"
        ]
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        # Get bot instance
        bot = get_bot_instance()
        
        # Get update data
        update_data = request.get_json()
        
        if update_data:
            # Process the update asynchronously using a thread pool
            import asyncio
            import concurrent.futures
            import threading
            
            def run_async_update():
                """Run the async function in a new event loop"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(bot.process_webhook_update(update_data))
                finally:
                    loop.close()
            
            # Run in a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_update)
                result = future.result(timeout=30)  # 30 second timeout
            
            if result:
                return jsonify({'status': 'ok'})
            else:
                return jsonify({'status': 'error', 'message': 'Failed to process update'}), 400
        else:
            return jsonify({'status': 'error', 'message': 'No update data'}), 400
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set Telegram webhook URL"""
    try:
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return jsonify({'error': 'TELEGRAM_BOT_TOKEN not set'}), 500
        
        # Get the webhook URL from Render environment
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if not render_url:
            return jsonify({'error': 'RENDER_EXTERNAL_URL not set'}), 500
        
        webhook_url = f"{render_url}/webhook"
        
        # Set webhook via Telegram API
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        response = requests.post(telegram_api_url, json={'url': webhook_url})
        
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({
                'status': 'success',
                'message': f'Webhook set to {webhook_url}',
                'telegram_response': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to set webhook',
                'telegram_response': response.json()
            }), 400
            
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Get current webhook information"""
    try:
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return jsonify({'error': 'TELEGRAM_BOT_TOKEN not set'}), 500
        
        # Get webhook info via Telegram API
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(telegram_api_url)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'webhook_info': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get webhook info',
                'telegram_response': response.json()
            }), 400
            
    except Exception as e:
        logger.error(f"Error getting webhook info: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For local development
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
