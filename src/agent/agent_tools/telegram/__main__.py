import logging
from .telegram_bot import Telegram

try:
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get Telegram bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logging.error("[TELEGRAM] TELEGRAM_BOT_TOKEN not found in environment variables")
        exit(1)
    
    # Initialize AI model
    from src.agent.agent_tools.model.model import Model
    model_api_key = os.getenv("MODEL_API_KEY")
    model = None
    if model_api_key:
        model = Model(model_api_key)
        logging.info("[TELEGRAM] AI model initialized for intelligent responses")
    else:
        logging.warning("[TELEGRAM] No MODEL_API_KEY found. Bot will use basic responses.")
    
    # Initialize and run Telegram bot with AI model
    bot = Telegram(token=token, model=model)
    bot.run()
    
except KeyboardInterrupt:
    logging.info("[TELEGRAM] Telegram bot shutting down...")
    exit()

